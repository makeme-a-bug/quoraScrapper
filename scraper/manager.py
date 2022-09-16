from datetime import datetime
import random
from .scraper import Scraper
from .questionScraper import QuestionScraper
from .file_data import file_data

from selenium import webdriver
import zipfile
import pandas as pd
import time
from concurrent.futures import ThreadPoolExecutor
import uuid
import os
import shutil
from dateutil import parser

class Manager:

    def __init__(self,file='Quora URLs - Topics.csv'):
        self.file = "inputs/"+file
        self.check_dirs()
        self.inputs = self.get_inputs()
        self.proxies = self.read_proxies()
        self.start_from_scratch = True


    def check_dirs(self):
        dirs = ['./inputs','./results','./temp',"./pluginFile"]
        for d in dirs:
            if not os.path.isdir(d):
                os.mkdir(d)

    def get_inputs(self):
        if not os.path.exists(f"{self.file}"):
            raise Exception(f"File {self.file} does not exists")
        file = pd.read_csv(self.file)
        return file

    def parse_date(self,date):
        try:
            if len(str(date)) > 0 and not pd.isna(date):
                return parser.parse(str(date).replace("ago",""))
            else:
                return ""
        except:
           return datetime.now()

    def start_collection(self):
        questions = []
        related_questions = []

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(self.get_questions, self.inputs['Links'].to_list())
            for r in results:
                questions.extend(r)

        questions_df = pd.DataFrame(columns=["questions"])
        questions_df['questions'] = questions
        questions_df.to_csv("./temp/all_questions_temp.csv")

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(self.get_related_questions, questions)
            for r in results:
                related_questions.extend(r)
        
        related_questions_df = pd.DataFrame(columns=["questions"])
        related_questions_df['questions'] = related_questions
        related_questions_df.to_csv("./temp/related__questions_temp.csv")

        combined = pd.concat([questions_df,related_questions_df])
        combined = combined.drop_duplicates(['questions'])
        combined.to_csv("./temp/combined.csv")

        # combined = pd.read_csv("combined.csv")

        for i in range(0, len(combined), 50):
            report = []
            with ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(self.get_question_details, combined['questions'].to_list()[i:i+50])#
                for r in results:
                    report.extend(r)
                report = pd.DataFrame(report)
                report.sort_values(['Followers','answers'],inplace=True,ascending=[False, True])
                if not os.path.isfile('results/desired_output.csv'):
                    report.to_csv('results/desired_output.csv')
                    report['Last Followed Date'] = report['Last Followed Date'].apply(self.parse_date)
                    report.to_csv('results/desired_output.csv')
                else: # else it exists so append without writing the header
                    report['Last Followed Date'] = report['Last Followed Date'].apply(self.parse_date)
                    report.to_csv('results/desired_output.csv', mode='a', header=False)
                self.clean_up()
    
    

    def read_proxies(self):
        column_names = ["proxy_host","proxy_port","username",'pwd']
        file = pd.read_csv("inputs/ips-data_center.txt",sep=":",header=None,names=column_names)
        return file



    def get_questions(self,url):
        proxy = self.create_proxy()
        questions = []
        with Scraper(options=proxy,destroy=False) as bot:
            bot.get_page(url)
            time.sleep(10)
            bot.start_scrolling()
            bot.get_all_questions()
            questions.extend(bot.questions)
        return questions


    def get_related_questions(self,url):
        questions = []
        try:
            proxy = self.create_proxy()
            with QuestionScraper(options=proxy) as bot:
                questions.extend(bot.get_related_questions(url))
        except:
            pass
        return questions

    def get_question_details(self,url):
        try:
            proxy = self.create_proxy()
            with QuestionScraper(options=proxy) as bot:
                answers,question_text,followers , views , last_followed , merged = bot.get_question_details(url)
        except Exception as e:
            print(f'could not get question:{url}')
            print(e)
            return []
        return [{
                "Question URL" : url,
                "Question":question_text,
                "Followers":followers,
                "Last Followed Date":last_followed,
                "Views":views,
                "Answers":answers,
                "Merged Questions":merged
                }]


    def create_proxy(self):
        proxy = random.choice(list(range(0,len(self.proxies[:1000]))))
        proxy = self.proxies.iloc[proxy]
        manifest_json,background_js = file_data(proxy['proxy_host'],proxy['proxy_port'],proxy['username'],proxy['pwd'])
        id= str(uuid.uuid4())
        chrome_options = webdriver.ChromeOptions()
        pluginfile = f'./pluginFile/proxy_auth_plugin_{id}.zip'
        with zipfile.ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        chrome_options.add_extension(pluginfile)
        return chrome_options



    def clean_up(self):
        folder = './pluginFile'
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

