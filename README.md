# JUSTFAIR WI dataset

This repository contains:
- A data scraping tool to gather data on court cases in WI
- The scraped data
- Analysis of the data

## Contribution Guidelines

Please contribute via pull requests (PR).

- Clone this repository
- Create your own branch
- Add contributions to your branch
- Push your branch
- Create a pull request to merge the changes in

### Scraping tool instructions

The scraping tool is written in Python. To use, you must have Python 3 installed on your system. If you are using Windows, this is avaible in the Windows Store.

After installing Python, install the dependencies by running this command from the Command Prompt (Windows) / terminal (Mac):

```
python3 -m pip install pyautogui requests
```

Then, run the scraper (open a command prompt / terminal wherever you have cloned this project):

```
python3 wi-scraper.py
```

Launch Chrome alongside the scraper, and open the developer tools (Ctrl+Shift+I on Windows, Command+Shift+I on Mac). Click on the Network tab.

Navigate to the [Wisconsin Court Site](https://wcca.wicourts.gov/caseDetail.html?caseNo=2020CF000016&countyNo=46&index=0&mode=details), and 
