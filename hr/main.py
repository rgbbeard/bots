#!/usr/bin/python3.10

from os import getcwd
from thread_maid import ThreadMaid
from time import sleep
from re import search, sub
from json import dumps as json_encode
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

CURRMONTH = datetime.now().date().month
CURRYEAR = datetime.now().date().year

GECKODRIVER = getcwd() + "/geckodriver"
GECKOSERVICE = Service(executable_path=GECKODRIVER)
DRIVER = webdriver.Firefox(service=GECKOSERVICE)

HRBASE = "https://{redacted}"
LOGINPAGE = f"{HRBASE}/path/to/login.jsp"
HOMEPAGE = f"{HRBASE}/path/to/home.jsp"

CREDENTIALS_PATH = "credentials.txt"
username: str = ""
password: str = ""
logged_in: bool = False

with open(CREDENTIALS_PATH, "r") as handler:
    username, password = handler.readlines()

hr_thread = ThreadMaid()
login_thread = ThreadMaid()

days = None
monthly_report: dict = {
    "ore_lavorate": 0, # not yet implemented
    "tempo_mancante": 0,  # not yet implemented
    "tempo_extra": 0,  # not yet implemented
    "dettaglio_giorni": {}
}


def find_element_by_xpath(xpath, fromElement = None):
    global DRIVER

    if fromElement == None:
        return DRIVER.find_element("xpath", xpath)
    else:
        return fromElement.find_element("xpath", xpath)


def find_all_by_xpath(xpath, fromElement = None):
    global DRIVER

    if fromElement == None:
        return DRIVER.find_elements("xpath", xpath)
    else:
        return fromElement.find_elements("xpath", xpath)


def perform_login():
    global DRIVER, username, password, logged_in

    while not logged_in:
        try:
            username_input = find_element_by_xpath("//input[contains(@id, '_m_cUserName')]")  # Username text input
            password_input = find_element_by_xpath("//input[contains(@id, '_m_cPassword')]")  # Password text input
            login_input = find_element_by_xpath("//input[contains(@id, '_Accedi')]")  # Login button

            username_input.send_keys(username)
            password_input.send_keys(password)

            login_input.click()
        except TimeoutException as te:
            print("Finding the login form..")
        except Exception as e:
            print("Generic exception at perform_login")

        sleep(1)


def perform_open_menu():
    global DRIVER, logged_in

    menu_item3_parent = None

    while menu_item3_parent == None:
        if logged_in:
            # setting a timer to exit the program after 10 attempts
            for t in range(1, 11):
                try:
                    # open the menu
                    menu_btn = find_element_by_xpath("//a[contains(@id, '_imgMenu')]")
                    menu_btn.click()

                    # goto the calendar page
                    menu_item3 = find_element_by_xpath("//font[contains(@id, '_MenuView_AppArea_3_descr')]")
                    menu_item3_parent = find_element_by_xpath("..", menu_item3)
                    menu_item3_parent.click()
                    break
                except Exception as e:
                    print("Generic exception at perform_open_menu")

                sleep(2)
            break


def navigate_calendar():
    global DRIVER, days

    while days == None:
        # setting a timer to exit the program after 15 attempts
        for t in range(1, 16):
            try:
                # find the main frame
                main_frame = WebDriverWait(DRIVER, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//iframe[contains(@id, '_iframe')]"))
                )
                DRIVER.switch_to.frame(main_frame)

                # move to the calendar window
                calendar_frame = WebDriverWait(DRIVER, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//iframe[contains(@id, '_Iframe17')]"))
                )
                DRIVER.switch_to.frame(calendar_frame)

                # find the days for the current month
                days = WebDriverWait(DRIVER, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//span[contains(@id, '_Label0') and not(contains(@class, 'altrimesi'))]"))
                )
                break
            except TimeoutException as te:
                print("Waiting for the main frame to load..")
            except Exception as e:
                print("Generic exception at navigate_calendar")

            sleep(2)
        break


def create_daily_report(day):
    global DRIVER, CURRMONTH, monthly_report

    d_ore_lavorate = 0.0
    d_tempo_mancante = 0.0
    d_tempo_extra = 0.0

    day = int(day)

    try:
        # find the main frame
        DRIVER.switch_to.default_content()
        main_frame = WebDriverWait(DRIVER, 10).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@id, '_iframe')]"))
        )
        DRIVER.switch_to.frame(main_frame)

        # move to the calendar window
        calendar_frame = WebDriverWait(DRIVER, 10).until(
            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@id, '_Iframe17')]"))
        )
        DRIVER.switch_to.frame(calendar_frame)

        # find ore_lavorate (if exists)
        try:
            d_ol_container = find_element_by_xpath("//div[contains(@id, '_LabelOreOrdValtbl')]")
            d_ore_lavorate = float(sub(":", ".", d_ol_container.text))
        except Exception as e:
            print(f"Container for ore_lavorate not found or invalid text for day {day}: {e}")

        # find giustificativi (if exists)
        try:
            d_gs = find_all_by_xpath("//tr[contains(@id, '_GridGiustificativi_row')]")

            if d_gs:
                for gs in d_gs:
                    content = gs.text.strip()
                    match = search(r"(\d{1,2}):(\d{2})", content)
                    if match:
                        hours, minutes = map(int, match.groups())
                        total_hours = float(f"{hours}.{minutes}")

                        if "ORE ECCEDENTI" in content:
                            d_tempo_extra += total_hours
                        elif "ORE MANCANTI" in content:
                            d_tempo_mancante += total_hours
        except Exception as e:
            print(f"Container for d_gs not found or invalid text for day {day}: {e}")

        monthly_report["dettaglio_giorni"][day] = {
            "ore_lavorate": d_ore_lavorate,
            "tempo_mancante": d_tempo_mancante,
            "tempo_extra": d_tempo_extra
        }
    except Exception as e:
        print(f"Error in creating report for day {day}: {e}")
  

def navigate_days():
    global DRIVER, days, monthly_report

    if days is None:
        raise Exception("There are no days for the current month")
    else:
        # setting a timer to exit the program after 15 attempts
        for t in range(1, 16):
            for d in days:
                try:
                    # scroll the element into view
                    DRIVER.execute_script("arguments[0].scrollIntoView(true);", d)

                    # wait until the obstructing element is not visible
                    WebDriverWait(DRIVER, 10).until_not(
                        EC.visibility_of_element_located((By.XPATH, "_RepeatDay"))
                    )

                    # wait until the element is clickable
                    WebDriverWait(DRIVER, 10).until(
                        EC.element_to_be_clickable(d)
                    )

                    # click using JavaScript to avoid overlay issues
                    DRIVER.execute_script("arguments[0].click();", d)

                    create_daily_report(d.text.strip())

                except Exception as e:
                    print(f"Could not click on element: {e}")
            break


def navigate_hr():
    global DRIVER, CURRMONTH, CURRYEAR, monthly_report

    perform_open_menu()
    navigate_calendar()
    navigate_days()

    with open(f"report_m{CURRMONTH}y{CURRYEAR}.json", "w") as handler:
        handler.write(json_encode(monthly_report))


login_thread.setup(target=perform_login)
hr_thread.setup(target=navigate_hr)

DRIVER.get(LOGINPAGE)

login_thread.run()
hr_thread.run()

while True:
    url = DRIVER.current_url

    if LOGINPAGE in url:
        pass
    elif HOMEPAGE in url:
        logged_in = True
        break
