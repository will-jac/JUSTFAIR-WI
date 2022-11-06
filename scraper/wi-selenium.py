import requests
import json
import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

caseYear = "2022"
caseLetters = [
    "CF",
    "CI",
    "CL",
    "CM",
    "CO",
    "CT",
    "CX",
    "FA",
    "FJ",
    "FO",
    "HL",
    "HT",
    "IN",
    "IP",
    "JD",
    "JT",
    "ML",
    "OL",
    "PA",
    "PR",
    "SC",
    "TC",
    "TJ",
    "TR",
    "TW",
    "UC",
    "WC",
    "WL",
]

firstLoadUrl = "https://wcca.wicourts.gov/caseDetail.html?caseNo=2020CF000016&countyNo=46&index=0&mode=details"
searchUrl = "https://wcca.wicourts.gov/jsonPost/advancedCaseSearch"
caseUrl = "https://wcca.wicourts.gov/jsonPost/caseDetail"

letterIdx = 0
if len(sys.argv) > 1:
    letterIdx = int(sys.argv[1])

# make the data dirs
for l in caseLetters:
    os.makedirs(f"./data/{l}", exist_ok=True)


def parse_cookies(cookie):
    cookies = {}
    cookie = cookie.split("; ")
    for c in cookie:
        kv = c.split("=")
        cookies[kv[0]] = kv[1]

driver = webdriver.Chrome()
action = webdriver.ActionChains(driver)

def first_load_catpcha():
    driver.get(firstLoadUrl)
    # fill out the captcha the first time
    input("please hit enter after you have filled out the captcha")

def auto_load_catpcha():
    driver.get(firstLoadUrl)
    # link to click
    try:
        # wait for the link to load
        el = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//main/div/span")))
        # add an extra wait so we don't look like a bot
        driver.implicitly_wait(3)
        # move the mouse to it so we don't look like a bot
        action.move_to_element(el)
        # click it
        action.perform()
    except:
        driver.quit()
        raise Exception("page did not load!")
    # wait 0.5 seconds for it to propogate
    time.sleep(5)
    
def get_cookie():
    cookies = {}
    for c in driver.get_cookies():
        if c["name"] in ["JSessionId_9401", "_ga", "_gid"]:
            cookies[c["name"]] = c["value"]
    return cookies

first_load_catpcha()
cookies = get_cookie()

# cookies = parse_cookies(input("Enter cookie:\n"))

caseLetter = caseLetters[letterIdx]

caseNumber = 0

print(f"Searching cases in range {caseYear}{caseLetter}XXXXX")

for caseNumber in range(15,20):
    
    caseID = f"{caseYear}{caseLetter}{caseNumber}"
    # find the cases with this number via the search
    searchBody = {
        "includeMissingDob": True,
        "includeMissingMiddleName": True,
        "caseNo": caseID
    }

    searchResult = json.loads(requests.post(searchUrl,json=(searchBody),cookies=cookies).content)

    for case in searchResult["result"]["cases"]:
        countyNum = case["countyNo"]
        caseID = case["caseNo"] 

        caseLookupBody = {
            "countyNo": countyNum,
            "caseNo": caseID
        }

        caseResult = requests.post(caseUrl,json=(caseLookupBody),cookies=cookies).content
        if caseResult[:20] == b'{"errors":{"captcha"':
            auto_load_catpcha()
            cookies = get_cookie()
            # input("Please solve captcha again, then press Enter")

            # re-do this case
            caseResult = requests.post(caseUrl,json=(caseLookupBody),cookies=cookies).content

            # if we still hit an error, prompt the user
            if caseResult[:20] == b'{"errors":{"captcha"':
                # cookies = parse_cookies(input("Enter cookie:\n"))
                first_load_catpcha()      
                cookies = get_cookie()
            
            print("running")

        with open(f"data/{caseLetter}/{caseID}-{countyNum}.json", "wb") as f:
            f.write(caseResult)


driver.quit()
