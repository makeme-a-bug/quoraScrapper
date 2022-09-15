from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException , NoSuchElementException

from rich.console import Console
from bs4 import BeautifulSoup
import requests

import os
from typing import Dict,List,Any,Union
import time
import re


class Scraper(webdriver.Chrome):

    def __init__(self,scroll_limit:str=100, driver_path : str="D:\Downloads\chromedriver.exe",destroy : bool=True,options=webdriver.ChromeOptions()) -> None:
        self.driver_path = driver_path
        os.environ["PATH"] += driver_path
        self.destroy_browser = destroy
        self.scroll_limit = scroll_limit
        self.scrolled = 0
        self.beauti = BeautifulSoup
        self.questions = []
        super(Scraper,self).__init__(self.driver_path,options=options)

        self.implicitly_wait(30)
        self.maximize_window()


    def get_page(self,url:str) -> bool:
        self.get(url)


    def get_question_details(self,url:str):
        numeric_text= {"K":1000 , "M":1000000}
        page = self.get_page(url+'/log')
        time.sleep(5)
        page = self.page_source
        source = self.beauti(page,'html.parser')
        data_div = source.select('div[class *= "q-flex qu-py--tiny qu-px--medium"]')
        followers = 0
        views = 0
        last_followed = None
        question = None
        merged = 0
        for div in data_div:
            text =  div.getText()
            if "public" in text:
                followers = re.findall(r'\d+', text)[0]
            if "views" in text:
                views = text.split(" ")[0]
                for k,v in numeric_text.items():
                    if k in views:
                        views = views.replace(k,"")
                        views = float(views) * v
                        break
            if "Last followed" in text:    
                last_followed = " ".join(text.split(" ")[2:])
            if "merged questions" in text:    
                merged = re.findall(r'\d+', text)[0]
        try:
            question = source.select('div[class*="puppeteer_test_question_title"]')[0].getText()
        except:
            print(url)

        answers = self.get_answers2(url)
        return answers,question,followers,views,last_followed,merged 

    def get_answers(self,source:BeautifulSoup):
        main_div = source.select_one("[id='mainContent']")
        # print(main_div.findAll("div", recursive=False)[1].select_one("[class*='q-box qu-pt--medium qu-pb--medium']").select("div[class='q-box']"))
        all_answers= main_div.findAll("div", recursive=False)[1].select_one("[class*='q-box qu-pt--medium qu-pb--medium']").select("div[class='q-box']")
        answers = 0
        for a in all_answers:
            divs = a.findAll("div")
            if len(divs) > 1:
                title:str = divs.getText()
                if "answer added" in title.lower() and "deleted" not in title.lower():
                    answers+=1
        
        return answers

    def get_answers2(self,url):
        page = self.get_page(url)
        time.sleep(5)
        dropdown = None
        try:
            dropdown = self.find_elements(By.CSS_SELECTOR,"[class*='DesktopPopoverMenu']")
            for d  in dropdown:
                if 'All related' in d.get_attribute('innerHTML'):
                    dropdown = d
                    break
            dropdown.click()
        except:
            dropdown = None
            pass

        page = self.page_source
        source = self.beauti(page,'html.parser')
        if dropdown:
            main_div = source.select("[class*='puppeteer_test_popover_menu']")[0].select("[class*='qu-dynamicFontSize--small']")[1].getText()
            answers = re.findall(r'\d+', main_div)[0]
        else:
            main_div = source.select_one("[id='mainContent']")
            # main_div = main_div.select_one("[class*='q-box qu-px--medium qu-pt--small qu-pb--small']")
            answers = main_div.select_one("[class*='q-box qu-px--medium qu-pt--small qu-pb--small']").find_all('div',recursive=False)[0].find_all('div',recursive=False)[0].getText()
            answers = re.findall(r'\d+', answers)[0]
        return answers





    def get_all_questions(self):
        source = self.beauti(self.page_source,'html.parser')
        questions = list(set([ s.find_previous('a').get('href') for  s in  source.select("div[class*='puppeteer_test_question_title']")]))
        self.questions.extend(questions)

    def start_scrolling(self):
        time.sleep(5)
        while self.scrolled <= self.scroll_limit:
            self.next_scroll()
            wait_long = WebDriverWait(self, 100)
            try:
                wiat = wait_long.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class *= "LoadingDots"]')))
            except TimeoutException:
                break
            time.sleep(3)

    def next_scroll(self):
        elem = self.find_element_by_tag_name("body")
        elem.send_keys(Keys.END)
        self.scrolled += 1

    def __exit__(self, *args) -> None:
        if self.destroy_browser:
            self.quit()