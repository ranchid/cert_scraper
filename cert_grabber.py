import os
import httpx

class CertGrabber:
    def __init__(self, print_url:str,
                 cert_url:str,
                 y_issued:int,
                 cust_header:dict=None):
        self.print_url = print_url
        self.cert_url = cert_url
        self.y_issued = y_issued
        self.cust_header = cust_header

    async def trigger_print(self, owner_id:str, auth_sess:object) -> str:
        async with httpx.AsyncClient(cookies=auth_sess, headers=self.cust_header, follow_redirects=True, timeout=None) as trigger:
            resp = await trigger.get(url=f"{self.print_url}/{owner_id}/{self.y_issued}")
            if resp.status_code == 200:        
                return owner_id

    async def grab_certificate(self, owner_id:str, dirpath:str) -> dict:        
        filepath =f"{dirpath}/{owner_id}.pdf"        
        async with httpx.AsyncClient(headers=self.cust_header, timeout=None) as downloader:
            dl = await downloader.get(url=f"{self.cert_url}_{owner_id}_signed.pdf",timeout=None)
            message = {}
            message['owner_id'] = owner_id
            if dl.status_code == 200:
                with open(filepath, "b+w") as f:
                    f.write(dl.content)
                    f.close
                message['filepath'] = os.path.relpath(filepath)
                return message