import locale
import re
import logging


from datetime import datetime
from pypdf import PdfReader


class PdfExtractor:
    def __init__(self, f_input:str):
        self.pdf_path = f_input
        self.pdf_input = PdfReader(self.pdf_path).pages[0]
    
    def _docs_format(self):
        size = self.pdf_input.mediabox
        match size.height:
            case 595.276:
                message = 'format_lama'
                return message
            case 841.89:
                message = 'format_baru'
                return message
    
    def content_extract(self):
        pdf_content = self.pdf_input.extract_text()
        npsn = re.search(pattern="\d{8,9}", string=pdf_content).group()
        date_pattern = r"[0-9]+ [A-Za-z]+ [0-9]+"
        p_no_cert = r"PD\.(.*)"
        p_ranking = r"Terakreditasi\s[A-Za-z]"
        no_cert = re.search(pattern=p_no_cert, string=pdf_content).group()
        ranking = re.search(pattern=r'\s+[A-Za-a]', 
                            string=re.search(
                                pattern=p_ranking, 
                                string=pdf_content).group()).group().strip()
        match self._docs_format():
            case 'format_lama':
                try:                    
                    p_valid_until = r"tanggal(\s([0-9]+ [A-Za-z]+\s)+)[0-9]+\s"
                    p_validated_at = r"Jakarta(\n([0-9]+ [A-Za-z]+\s)+)[0-9]+"
                    s_valid_until = re.search(pattern=p_valid_until, string=pdf_content).group()
                    s_validated_at = re.search(pattern=p_validated_at, string=pdf_content).group()
                    valid_until = re.search(pattern=date_pattern, string=s_valid_until).group()
                    validated_at = re.search(pattern=date_pattern, string=s_validated_at).group()
                    locale.setlocale(locale.LC_ALL, 'id_ID')
                    d_valid_until = datetime.strptime(valid_until, '%d %B %Y').date()
                    d_validated_at = datetime.strptime(validated_at, '%d %B %Y').date()                
                    extracted_data = {
                        'npsn': npsn,
                        'no_cert': no_cert,
                        'ranking': ranking,
                        'validated_at': d_validated_at,
                        'valid_until': d_valid_until,
                        'cert_model': self._docs_format(),
                        'filepath': self.pdf_path
                        }
                    
                    return extracted_data
                except AttributeError:
                    logging.error(f"{self.pdf_path} text parsing error")
            
            case 'format_baru':
                try:
                    p_valid_until = r"dengan tanggal(\s([0-9]+ [A-Za-z]+\s)+)[0-9]+\s"
                    p_validated_at = r"Pada tanggal [0-9]+ [A-Za-z]+ [0-9]+"
                    s_valid_until = re.search(pattern=p_valid_until, string=pdf_content).group()
                    s_validated_at = re.search(pattern=p_validated_at, string=pdf_content).group()
                    valid_until = re.search(pattern=date_pattern, string=s_valid_until).group()
                    validated_at = re.search(pattern=date_pattern, string=s_validated_at).group()                    
                    locale.setlocale(locale.LC_ALL, 'id_ID')
                    d_valid_until = datetime.strptime(valid_until, '%d %B %Y').date()
                    d_validated_at = datetime.strptime(validated_at, '%d %B %Y').date()                
                    extracted_data = {
                        'npsn': npsn,
                        'no_cert': no_cert,
                        'ranking': ranking,
                        'validated_at': d_validated_at,
                        'valid_until': d_valid_until,
                        'cert_model': self._docs_format(),
                        'filepath': self.pdf_path
                        }
                    
                    return extracted_data
                except AttributeError:
                    logging.error(f"{self.pdf_path} text parsing error")
        


