import os
import httpx
import logging

class CertGrabber:
    def __init__(self, print_url:str, cert_url:str, y_issued:int, cust_header:dict=None):
        self.print_url = print_url
        self.cert_url = cert_url
        self.y_issued = y_issued
        self.cust_header = cust_header

    async def trigger_print(self, owner_id:str, auth_sess:object) -> str:
        async with httpx.AsyncClient(cookies=auth_sess, headers=self.cust_header, follow_redirects=False, timeout=None) as trigger:
            resp = await trigger.get(url=f"{self.print_url}/{owner_id}/{self.y_issued}")
            if resp.status_code == 307:    
                return owner_id
            elif resp.status_code == 404:
                logging.warn(f'{owner_id} not found')

    async def grab_certificate(self, owner_id:str, dirpath:str) -> dict:        
        filepath =f"{dirpath}/{owner_id}.pdf"        
        async with httpx.AsyncClient(headers=self.cust_header, timeout=None) as downloader:
            dl = await downloader.get(url=f"{self.cert_url}_{owner_id}_signed.pdf")
            if dl.status_code == 200:
                with open(filepath, "b+w") as f:
                    try:
                        logging.info(f'Writing {owner_id}.pdf ...')
                        f.write(dl.content)
                        f.close
                        logging.info(f"File succesfully saved at {os.path.relpath(filepath)}")           
                    except:
                        logging.error(f'{owner_id}.pdf failed to download')