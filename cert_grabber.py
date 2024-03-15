import os
import logging
import sys
import httpx

class CertGrabber:
    def __init__(self, print_url:str, cert_url:str, y_issued:int, cust_header:dict=None):
        self.print_url = print_url
        self.cert_url = cert_url
        self.y_issued = y_issued
        self.cust_header = cust_header

    async def trigger_print(self, owner_id:str, auth_sess:object, batch_to_timeout:int=None) -> str:
        # n_conn = httpx.Limits(max_keepalive_connections=conn_limit, max_connections=conn_limit*2)
        try:
            async with httpx.AsyncClient(cookies=auth_sess, headers=self.cust_header, follow_redirects=False) as trigger:
                resp = await trigger.get(url=f"{self.print_url}/{owner_id}/{self.y_issued}", timeout=batch_to_timeout)
                if resp.status_code == 307:
                    return owner_id
                
                logging.warn(f'Error printing {owner_id}.pdf ')
        except:
            logging.warn(f'Error printing {owner_id}.pdf ')

    async def grab_certificate(self, owner_id:str, dirpath:str, batch_to_timeout:int=None) -> dict:        
        filepath =f"{dirpath}/{owner_id}.pdf"
        dl_status = {}
        dl_status['npsn'] = owner_id
        # n_conn = httpx.Limits(max_keepalive_connections=conn_limit, max_connections=conn_limit*2)
        async with httpx.AsyncClient(headers=self.cust_header, timeout=batch_to_timeout) as downloader:
            try:
                dl = await downloader.get(url=f"{self.cert_url}_{owner_id}_signed.pdf")
                if dl.status_code == 200:                
                    with open(filepath, "b+w") as f:
                        content = dl.content
                        if sys.getsizeof(content) > 400000:
                            logging.info(f'Writing {owner_id}.pdf ...')                    
                            f.write(content)
                            f.close
                            logging.info(f"File succesfully saved at {os.path.relpath(filepath)}")
                            dl_status['status'] = 'OK'
                            return dl_status
                        dl_status['status'] = 'FAILED'
                        return dl_status
                dl_status['status'] = 'FAILED'
                logging.error(f'Failed to get {owner_id}.pdf')
                return dl_status
            except:
                logging.error(f'Failed to get {owner_id}.pdf')
                dl_status['status'] = 'FAILED'
                return dl_status