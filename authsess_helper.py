import httpx
from bs4 import BeautifulSoup

class LoginHelper:
    """
    A session builder for using/re-using an authenticated session\n\n
    **Parameters**\n
    * **url_login**-*[Required]* URL for sending authentication data payload
    * **url_login**-*[Required]* Fallback URL if authentication failed (status code 401)
    * **url_logout**-*[Required]* URL to logout
    * **login_success**-*[Required]* Redirected page (Dashboad/Home) after successfully logged-in
    * **cust_header*-*[Optional]* Custom header for mimicking real browser
    """
    def __init__(self, url_login:str,
                 url_fail:str,
                 url_logout:str,
                 login_success:str, 
                 cust_header:dict=None):
        self.url_login = url_login
        self.url_fail = url_fail
        self.url_logout = url_logout
        self.login_success = login_success
        self.session = httpx.Client(follow_redirects=True, headers=cust_header)

    def check_auth(self, response, dest_url) -> int:
        if str(response.url) == dest_url:            
            return 200
        elif str(response.url) == self.url_fail:            
            return 401
        else:
            resp = response.url            
            return resp
        
    def login(self, username:str, password:str):
        """
        Method for sending given auth data to the host\n\n
        **Parameters**\n
        * **username**-*[Required]* user/id/email
        * **password**-*[Required]* password/token/credential
        """
        __dummy_bait = self.session.get(self.url_fail).content
        token_brutal= BeautifulSoup(__dummy_bait, features='html.parser').find('input').get('value')
        auth_data = {}
        auth_data['sispena_csrf'] = token_brutal
        auth_data['vnrtgugoiuwcru'] = str(username)
        auth_data['oncgbuwmrcwuhr'] = str(password)       
        send_auth = self.session.post(url=self.url_login, data=auth_data)        
        return self.check_auth(send_auth, self.login_success)

    def logout(self):
        logout = self.session.get(self.url_logout).status_code
        return logout