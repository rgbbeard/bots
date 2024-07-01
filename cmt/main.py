"""
Minimum Python version 3.x
Using Python version 3.7.x
"""

from selenium import webdriver
from threading import Thread
import os
from app_utils import (is_file, fname, fext)
from re import (search, sub, findall)
from lnx_utils import create_file
from time import sleep

GECKODRIVER = r"C:\Users\Davide\Desktop\drivers\geckodriver.exe"
LOGINPAGE = "login.{redacted}.it"
PLATFORMPAGE = "platform.{redacted}.it"
JOBSPAGE = "4p.{redacted}.it"
LOGINUN = ""
LOGINPW = ""

driver = webdriver.Firefox(executable_path=GECKODRIVER)


def get_url():
    global driver

    return str(driver.current_url).strip()


def perform_login():
    global driver, LOGINUN, LOGINPW

    try:
        username_input = driver.find_element_by_id("Username")  # Username text input
        password_input = driver.find_element_by_id("Password")  # Password text input
        login_input = driver.find_element_by_xpath ("//button[contains(text(), 'Login')]")  # Login button

        username_input.send_keys(LOGINUN)
        password_input.send_keys(LOGINPW)

        login_input.click()
    except Exception as e:
        print(e)
        exit()


def goto_jobspage():
    global driver

    driver.get(url="https://4p.{redacted}.it/printers/Jobs.aspx")


def search_jobs():
    global driver
    
    try:
        os.chdir(r"p:\davide\cmtrading\fatto")
        files = os.listdir()

        for f in files:
            if is_file(f) and fext(f) == "xlsx" and "maps_" in fname(f):
                n = sub(r"(maps_)|(e[\d]+_)", "", fname(f))

                if search(r"^([\d]{5})$", n):
                    search_button = driver.find_element_by_id("BtnCarSpec2")
                    search_button.click()

                    search_input = driver.find_element_by_id("ctl00_ContentPlaceHolder1_TbFilterJobID")
                    search_input.send_keys(n)
                    sleep(5)
                    xpath = "//table[@id='ctl00_ContentPlaceHolder1_GridViewJobs']/tbody/tr[2]"
                    date_container = driver.find_element_by_xpath(xpath)
                    d = str(date_container.text).strip()
                    d = str(findall(r"([\d]{2}\/[\d]{2}\/[\d]{4} [\d]{2}:[\d]{2}:[\d]{2})", d)[1]).strip()
                    r = create_file(f"{n}.date", d)

                    if r != True:
                        print(f"Unable to write data for file: {f} -> {n} -> {r}\n")
        print("Process completed")
        exit()
    except Exception as e:
        print(e)
        exit()


def check_location():
    global driver, LOGINPAGE, PLATFORMPAGE, JOBSPAGE
    
    driver.get(url="https://" + LOGINPAGE)

    while True:
        url = get_url()

        if LOGINPAGE in url:
            perform_login()
        elif PLATFORMPAGE in url:
            goto_jobspage()
        elif JOBSPAGE in url:
            search_jobs()


process_thread = Thread(target=check_location)
process_thread.start()
