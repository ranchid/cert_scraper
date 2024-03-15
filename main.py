import os
import sys
import logging
import csv
import asyncio
import uuid
from datetime import datetime

from dotenv import load_dotenv
from pypdf import errors

from authsess_helper import LoginHelper
from cert_grabber import CertGrabber
from data_extractor import PdfExtractor

now = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
scrap_sess = uuid.uuid4()
load_dotenv()
logfile_handler = logging.FileHandler(filename="./scrap.log")
logstream_handler = logging.StreamHandler(stream=sys.stdout)
logging.basicConfig(handlers=[logfile_handler, logstream_handler],
                    format='%(asctime)s.%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

sispena_url = os.getenv('URL_BASE')
cust_header = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0'}

download_dir = os.getenv('DOWNLOAD_DIR')
year_issued = os.getenv('YEAR_ISSUED')
download_path = f"{os.getcwd()}/{download_dir}/{year_issued}"

os.makedirs(download_path, exist_ok=True)


url_login = os.getenv('URL_LOGIN')
url_logout = os.getenv('URL_LOGOUT')
url_fail = os.getenv('URL_FAIL')
dashboard = os.getenv('URL_LOGIN_SUCCESS')
print_url = os.getenv('URL_PRINT')
cert_url = os.getenv('URL_CERTIFICATE')

print_sess = LoginHelper(url_login=url_login,
                         url_fail=url_fail,
                         url_logout=url_fail,
                         login_success=dashboard,
                         cust_header=cust_header)

scrap_cert = CertGrabber(print_url=print_url,
                         cert_url=cert_url,
                         y_issued=year_issued,
                         cust_header=cust_header)

async def job_aggregator(job_list):
    job_agg = await asyncio.gather(*job_list)
    return job_agg

def data_input(filename):
    with open(filename, "r") as source:
        datasource = source.read().splitlines()
        source.close()
    return datasource

def n_splitter(input_list:list, divider:int) -> list:
    if len(input_list) <= divider:
        return [input_list]
    else:
        k, m = divmod(len(input_list), divider)
        if m > 0:
            temp_q = k+1
        else:
            temp_q = k
        task_q = []
        for task in range(temp_q):
            head_rec = +task*divider
            tail_rec = head_rec+divider
            if tail_rec > len(input_list):
                tail_rec = len(input_list)
            task_q.append(input_list[head_rec:tail_rec])
        return task_q
    
def download_checker(list_id:list, dl_path:str) -> list:    
    files = {}
    files['to_download'] = []
    files['existing'] = [os.path.splitext(file)[0] for file in os.listdir(dl_path)]
    for file_id in list_id:
        if file_id not in files['existing']:
            files['to_download'].append(file_id)
    return files

def report_builder(file_path:str) -> list:
    file_list = [f"{os.path.relpath(file_path)}/{ext_file}" for ext_file in os.listdir(file_path)]
    report = []
    for ext_file in file_list:
        logging.info(f"Parsing data from {ext_file}")
        try:
            report.append(PdfExtractor(ext_file).content_extract())
        except errors.EmptyFileError:
            logging.error(f'Document {ext_file} corrupt')
    fields = [k for k, v in report[0].items()]
    with open (f"report_{scrap_sess}.csv", "w") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report)
        csvfile.close()
    logging.info(f"Report written with name report_{scrap_sess}.csv")
    # return report

def main(datasource, batch_size:int, user:str, pswd:str, dl_path:str, dl_timeout:float, print_timeout:float):
    list_id = data_input(datasource)
    download_list = download_checker(list_id, dl_path=dl_path)
    logging.info(f'START {scrap_sess}')
    
    if len(download_list['to_download']) > 0:
        dl_job = n_splitter(download_list['to_download'], batch_size)
        to_print = []
        for dl_batch in dl_job:
            download_task = [scrap_cert.grab_certificate(owner_id=npsn, dirpath=dl_path, batch_to_timeout=dl_timeout*len(dl_batch)) for npsn in dl_batch]
            dl_stats = asyncio.run(job_aggregator(download_task))        
            dl_fail = [npsn['npsn'] for npsn in dl_stats if npsn.get('status') == 'FAILED']
            to_print += dl_fail
        if len(to_print) > 0:
            print(to_print)
            match print_sess.login(username=user, password=pswd):
                case 200:
                    sc_job = n_splitter(to_print, batch_size)
                    new_input = []
                    for batch in sc_job:
                        print_sess.login(username=user, password=pswd)
                        printing_task = [scrap_cert.trigger_print(owner_id=element, auth_sess=print_sess.session.cookies, batch_to_timeout=print_timeout*len(batch)) for element in batch if element is not None]
                        if len(printing_task) > 0:
                            print_agg = asyncio.run(job_aggregator(printing_task))
                            print_sess.logout()
                            retry_download = [scrap_cert.grab_certificate(owner_id=npsn, dirpath=dl_path, batch_to_timeout=dl_timeout*len(batch)) for npsn in print_agg]
                            retry_stats = asyncio.run(job_aggregator(retry_download))
                            to_log = [npsn['npsn'] for npsn in retry_stats if npsn.get('status') == 'OK']
                            new_input += to_log
                    if len(new_input) > 0:
                        print("Generating report this may take a while...")
                        report_builder(dl_path)
                        logging.info(f'END {scrap_sess}')
                    print("No new file(s) found")
                    logging.info(f'END {scrap_sess}')
                case _:
                    logging.critical('Authentication Failed')
                    logging.info(f'END {scrap_sess}')
        report_builder(dl_path)
        logging.info(f'END {scrap_sess}')
    else:
        return 'no_new_file'
    

if __name__ == "__main__":
    import argparse
    os.makedirs(download_path, exist_ok=True)
    parser = argparse.ArgumentParser(description='Certificate Scrapper and Data Parser')
    parser.add_argument('filename', help="[Required] Specify filaname.txt that contains list of id to scrape")
    parser.add_argument('-n', '--batch', type=int, default=os.getenv('BATCH_SIZE'), help="[Optional] Override maximum n-value on .env per batch processing")
    parser.add_argument('-u', '--user', type=str, default=os.getenv('IDENTIFIER'), help="[Optional] Override .env's user/identifier")
    parser.add_argument('-p', '--password', type=str, default=os.getenv('SECRETS'), help="[Optional] Override .env's password/secrets")
    parser.add_argument('-pt', '--print_timeout', type=float, default=os.getenv('PRINT_TIMEOUT'), help="[Optional] Override default timeout for print session")
    parser.add_argument('-dt', '--download_timeout', type=float, default=os.getenv('DOWNLOAD_TIMEOUT'), help="[Optional] Override default timeout for download session")
    args = parser.parse_args()
    try:
        main_process = main(datasource=args.filename, batch_size=args.batch, user=args.user, pswd=args.password, dl_timeout=args.download_timeout, print_timeout=args.print_timeout, dl_path=download_path)
        if main_process == 'no_new_file':
            regen_report = input('No new file(s) detected,\nDo you still want to generate report file? (y|N) ')            
            if regen_report.casefold() == 'y':
                print("Generating report please wait...")
                report_builder(download_path)                
                logging.info(f'END {scrap_sess}')
            else:
                print('message')
    except KeyboardInterrupt:
        logging.warning(f"Process {scrap_sess} prematurely ended by user")
    

