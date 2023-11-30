from datetime import datetime
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_URL = "https://www.mijnwoonservice.nl"
HEADERS = {"User-Agent": "HouseBot", "Accept-Encoding": "gzip"}
DUMP_FILE = "adverts.json"
TIMEOUT = 5
username = ""
password = ""

logging.basicConfig(
    filename="housebot.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)
logger.info(f"Started script")
driver = webdriver.Chrome()

# Get Previous Data
try:
    with open(DUMP_FILE, "r") as file:
        advert_history = json.load(file)
except FileNotFoundError:
    advert_history = {}

# Cookies & Login
driver.get(BASE_URL)
WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "cookiescript_accept"))).click()
WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "Input_UsernameVal"))).send_keys(username)
WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "Input_PasswordVal"))).send_keys(password)
WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, "b8-Button"))).click()

# Get Links
article_element = WebDriverWait(driver, TIMEOUT).until(
    EC.presence_of_element_located((By.CLASS_NAME, 'osui-tabs__content-item.osui-tabs--is-active'))
)
links = article_element.find_elements(By.TAG_NAME, 'a')
advert_links = [link.get_attribute('href') for link in links]
logger.info(f"Found {len(advert_links)} adverts that meet requirements: {advert_links}")

# Get Ads


def parse_ad(link) -> dict:
    driver.get(link)
    reacted = False
    try:
        match = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "match met je wensen")]'))).text
    except TimeoutException:
        match = None

    if match and int(match.split("%")[0]) > 50:
        reacted = True
        try:
            WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.CLASS_NAME, 'btn-primary'))).click()
        except TimeoutException:
            logger.warning(f"Cannot react to {link}")
    primary_metadata = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.ID, '$b15')))
    parsed_primary_metadata = primary_metadata.text.split("\n")
    return {
        "detected on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "match": match,
        "reacted": reacted,
        "address": parsed_primary_metadata[0],
        "sold_by": parsed_primary_metadata[1],
        "reactable_until": parsed_primary_metadata[2],
    }


for advert_link in advert_links:
    advert_id = advert_link.split("=")[-1]
    if advert_id not in advert_history:
        advert_history[advert_id] = parse_ad(advert_link)
        logging.info(f"Added {advert_id} to {file}")

with open(DUMP_FILE, 'w') as file:
    json.dump(advert_history, file, indent=4)
driver.close()
