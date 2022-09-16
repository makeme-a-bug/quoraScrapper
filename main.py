import os
import zipfile

from scraper.manager import Manager,Scraper
import pandas as pd
from selenium import webdriver
from scraper.file_data import file_data


if __name__ == "__main__":
    m = Manager()
    m.start_collection()
    