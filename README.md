# Docs Scrapper and Data Parser
Simple script for automation docs scrapping and parsing content data. The code has been tested on python 3.11.7

## Installation Guide
* Clone this repository `git clone https://github.com/ranchid/cert_scraper.git`
* Change directory to cloned repository `cd cert_scraper`
* Install required libraries `pip install -r requirements.txt`
* Copy .env.sample to .env `cp .env.sample .env` and edit necessary parameter to change.

## Usage
* head to project root's directory
* run `python main.py list_of_id.txt` on terminal to run it as-is .env configuration
    * after process completed successfully file will be saved at specified DOWNLOAD_DIR path on .env file
    * report will be saved at [project root's directory]/report_SESSION-UUID.csv
* run `python main.py -h` show help message
    * if any error or malfunction you can inspect scrap.log file
