import os
import zipfile

from scraper.manager import Manager,Scraper
import pandas as pd
from selenium import webdriver
from scraper.file_data import file_data


if __name__ == "__main__":
    m = Manager()
    m.start_collection()
    # PROXY = "zproxy.lum-superproxy.io:22225"
    # manifest_json,background_js = file_data('zproxy.lum-superproxy.io',22225,'lum-customer-c_e1805dcc-zone-data_center-ip-181.215.0.194','2ztxt6jlaysr')
    # chrome_options = webdriver.ChromeOptions()
    # pluginfile = 'proxy_auth_plugin.zip'
    # with zipfile.ZipFile(pluginfile, 'w') as zp:
    #     zp.writestr("manifest.json", manifest_json)
    #     zp.writestr("background.js", background_js)
    # chrome_options.add_extension(pluginfile)
    
    # with Scraper(destroy=False,options=chrome_options) as bot:
    #     bot.get_page("https://api.ipify.org/?format=json")