from datetime import datetime
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://www.mijnwoonservice.nl"
HEADERS = {"User-Agent": "HouseBot", "Accept-Encoding": "gzip"}
DUMP_FILE = "adverts.json"
TIMEOUT = 5
QUERY_COOLDOWN = 2
username = ""
password = ""

# Cookies & Login
driver = webdriver.Chrome()
driver.get(BASE_URL)
WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "cookiescript_accept"))).click()
WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "Input_UsernameVal"))).send_keys(username)
WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "Input_PasswordVal"))).send_keys(password)
WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "b8-Button"))).click()

# Get Previous Data
try:
    with open(DUMP_FILE, "r") as file:
        adverts = json.load(file)
except FileNotFoundError:
    adverts = {}

# Get Links
elements = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@id, "HuisContainerLink")]')))
advert_links = [element.get_attribute('href') for element in elements]
print(advert_links)

# Get Ads


def parse_ad(link) -> dict:
    driver.get(link)
    try:
        match = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "match met je wensen")]')))
        match = int(match.text.split("%")[0])
    except TimeoutException:
        match = 0

    try:
        address = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div/div/div/div/div[1]/div/div/div/div[1]/div/div/div[1]/div[2]/div/div[1]/div/span'))).text
    except TimeoutException:
        address = None

    return {
        "detected on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "match": match,
        "address": address,
        "reacted": False,
    }


for advert_link in advert_links[:1]:
    id = advert_link.split("=")[-1]
    # if id not in adverts:
    adverts[id] = parse_ad(advert_link)

with open(DUMP_FILE, 'w') as file:
    json.dump(adverts, file, indent=4)
driver.close()
