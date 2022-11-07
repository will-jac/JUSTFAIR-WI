import requests
import json
import sys
import os
import time

import pyautogui

firstLoadUrl = "https://wcca.wicourts.gov/caseDetail.html?caseNo=2020CF000016&countyNo=46&index=0&mode=details"
searchUrl = "https://wcca.wicourts.gov/jsonPost/advancedCaseSearch"
caseUrl = "https://wcca.wicourts.gov/jsonPost/caseDetail"

reload_pos = None
captcha_pos = None

def parse_cookies(cookie):
    cookies = {}
    cookie = cookie.split("; ")
    for c in cookie:
        kv = c.split("=")
        cookies[kv[0]] = kv[1]
    return cookies

def auto_load_captcha(wait=10):
    global reload_pos, captcha_pos
    # reload chrome
    if reload_pos is None:
        input(f"\nMove the mouse to the reload button, then press enter\n")
        reload_pos = pyautogui.position()

    pyautogui.moveTo(reload_pos)
    pyautogui.click()
    # wait
    time.sleep(wait)
    # click the captcha
    if captcha_pos is None:
        print("Click on this window again")
        input(f"Move the mouse to the captcha link , then press enter\n")
        captcha_pos = pyautogui.position()
    pyautogui.moveTo(captcha_pos)
    pyautogui.click()
    # wait
    time.sleep(3)

caseYear = input("Enter case year: ")
caseLetter = input("Enter Case Letter: ")
startingCaseNumber = int(input("Enter Case Number Start: "))
cookie = input(f"Enter cookie:\n")
cookies = parse_cookies(cookie)

# make the data dir
os.makedirs(f"./data/{caseYear}/{caseLetter}", exist_ok=True)
print(f"Searching cases starting with {caseYear}{caseLetter}XXX{startingCaseNumber}")

def try_search():
    for i in range(10):
        try:
            searchResult = json.loads(requests.post(searchUrl,json=(searchBody),cookies=cookies).content)
            break
        except:
            print('retrying search')
            time.sleep(5)
    return searchResult

def try_url():
    for i in range(10):
        try:
            caseResult = requests.post(caseUrl,json=(caseLookupBody),cookies=cookies).content
            break
        except:
            print('retrying url')
            time.sleep(5)
    return caseResult

# basically can do a while loop until we run out of case numbers
while True:
    for caseNumber in range(startingCaseNumber, 5000):
        
        caseID = f"{caseYear}{caseLetter}{caseNumber}"
        # find the cases with this number via the search
        searchBody = {
            "includeMissingDob": True,
            "includeMissingMiddleName": True,
            "caseNo": caseID
        }

        searchResult = try_search()

        if len(searchResult["result"]["cases"]) == 0:
            print("Done!", caseNumber)
            break

        # print out progress
        sys.stdout.write('\r')
        sys.stdout.write(str(caseNumber))
        sys.stdout.flush()


        for case in searchResult["result"]["cases"]:
            countyNum = case["countyNo"]
            caseID = case["caseNo"]

            caseLookupBody = {
                "countyNo": countyNum,
                "caseNo": caseID
            }

            caseResult = try_url()
            
            if caseResult[:20] == b'{"errors":{"captcha"':
                auto_load_captcha(15)
                caseResult = try_url()

                # TODO: use pyautogui to set the address bar and re-type the address on failure

                # if we still hit an error, prompt the user
                if caseResult[:20] == b'{"errors":{"captcha"':
                    usr_in = input(f"Check Captcha. Enter cookie, or press enter to use current {cookie}\n")
                    if usr_in is not None and usr_in != "":
                        cookie = usr_in
                    cookies = parse_cookies(cookie)
                
                    print("running")

                    caseResult = try_url()


            with open(f"data/{caseYear}/{caseLetter}/{caseID}-{countyNum}.json", "wb") as f:
                f.write(caseResult)

    caseYear = str(int(caseYear) + 1)
    startingCaseNumber = 1
    # make the data folder
    os.makedirs(f"./data/{caseYear}/{caseLetter}", exist_ok=True)
