# JUSTFAIR WI dataset

This repository contains:
- A data scraping tool to gather court cases in WI
- The extracted, raw data
- A data conversion tool
- The converted data

## Contribution Guidelines

Please contribute via pull requests (PR).

- Clone this repository
- Create your own branch
- Add contributions to your branch
- Push your branch
- Create a pull request to merge the changes in

## Data Explanation

There are two data files produced for each case type and year. The case types are CF for felony and CM for misdemeanor.

All cases are completed, but include both convicted and acquited individuals.

The file `cases-compiled` contains case level information for each case. Most of this should be fairly self-explanatory. For more information, the metadata file should provide some context.

| Variable Name | Type | Notes |
|---------------|------|-------|
|caseNo         |string|Case identifier. Not unique, see notes for format|
|countyNo       |int, range 1-72|County identifier. Creates unique ID for cases with case number|
|countyName     |string| |
|defendentName  |string|Format: Last, First MI. (sometimes with . at the end). May have an extra "" around it|
|defendentRace  |string| |
|defendentSex   |string| |
|defendentDob   |string|Date of birth, format YYYY-MM-DD |
|judgeName      |string|Same format as defendent name|
|cost           |number|Court costs that the defendent owes|
|aggregateChargeJail|number|Total years in jail for this case|
|aggregateChargePrison|number|Total years in prison for this case|
|aggregateChargeProbation|number|Total years of probation for this case|
|aggregateChargeLife|number|Total number of life sentences for this case|
|maxChargeCrimeName|string|Charge crime name for crime with most severe sentence issued|
|maxChargeCrimeDate|string|Date, format YYYY-MM-DD|
|maxChargeCrimeStatue|string|Wisconsin statute|
|maxChargeCrimeSeverity|string|Crime severity, eg Felony G|
|maxChargePleaDate|string|Date of plea, format YYYY-MM-DD, if a plea exists|
|maxChargePleaDescr|string| |
|maxChargeJail       |number|Total years in jail for the maximum charge in this case|
|maxChargePrison     |number|Total years in prison for the maximum charge in this case|
|maxChargeProbation  |number|Total years of probation for the maximum charge in this case|
|maxChargeLife       |number|Total number of life sentences for the maximum charge in this case|
|numChartes          |number|The number of charges in this case|

Of note is the fact that each case has aggregate charge information - the total amount of jail, prison, probation time, or life sentences for each charge, (loosely) accounting for concurrent sentences, as well as the maximum jail, prison, probation time, or life sentences for any individual charge. 

We also show the most severe charge name, where severity is defined by the amount of time that was served. This follows a hierarchy - life > prison > jail > probation. This is not perfect. For example if someone was charged with murder 1 and manslaughter, but only served time for manslaughter then we would show the most severe case as manslaughter.

We also show the total amount due to the court, in costs. This currently does not include restitution or any civil judgments.


## JSON file format notes

The JSON file consists of data about a single court case. A case consists of data about the case, most of which is self-explanatory, and (potentially) several charges.

Each charge consists of charge information and (potentially) several judgements.

Each judgements consists of judgement information and (potentially) several supervisions.

Each supervision consists of the desciption (`descr`) (what they are sentenced to, notably County / Local Jail, State Prison, Probation, Extra Supervision, and hard to parse values like Costs), `time` (length of jail sentence), and other data.

The best way to determine what a data element represents is to look at many different file types for it, and write a bit of code to gather all possible values for it.

## Scraping Tool Instructions

The scraping tool is written in Python. To use, you must have Python 3 installed on your system. If you are using Windows, this is avaible in the Windows Store.

After installing Python, install the dependencies by running this command from the Command Prompt (Windows) / terminal (Mac):

```
python3 -m pip install pyautogui requests
```

Now, you're ready to run the scraper. First, get the session cookie you'll need.

Launch Chrome, and open the developer tools (Ctrl+Shift+I on Windows, Command+Shift+I on Mac). Click on the Network tab.

Navigate to the [Wisconsin Court Site](https://wcca.wicourts.gov/caseDetail.html?caseNo=2020CF000016&countyNo=46&index=0&mode=details), and find the network request to `caseDetail` in the network tab. Click to open this, then scroll down to find the Cookie under the Headers tab. Right click and copy the value.

Then, run the scraper (open a command prompt / terminal wherever you have cloned this project):

```
python3 wi-scraper.py
```

Enter the case year, type (CF for felony, CM for misdemeanor), and starting number (probably 1). Then, paste in the cookie you copied. Next, the script will walk you through setting the refresh locations in Chrome. This may take a minute or two to show up, depending on your internet connection.

Finally, relax and let your computer scrape data. Let it be, and don't do anything to move the mouse. The number at the bottom is the case number that has been extracted - this counts up. If you need to re-run the script and want to pick up where you left off, use this value.

Notes: 
- Sometimes, the site may realize that you're a bot, and start throwing up Captchas all the time. If that happens, try clearing the cookies for the site.
- It seems like the site is slower at night - it tends to fail more for me then.

## TODO

[] Add a column for "acquited" in the case level for those found not guilty of all charges
[] Add a column for "pleaDeal" in the case level for those with any charge-level plea deal
[] Add a column for prosecuting attourney in the case level
[] Add a column for pre-trial detention length in the case level (if possible)
[] Figure out a better way to detect duplicate judgements. Right now, we are:
   - Right now, only exracting "original" judgments, so any renewed orders are ignored
   - Likely, the best solution will be to just clean up the data with bad judgments
   - Any bad data is just ignored
[] Add Civil Judgments in addition to sentences
[] Check that this works well for misdemeanors - see if there's more we can extract
[] Use pyautogui to set the address for if/when the captcha soft-fails
[] Improve the detection of concurrent sentences. Right now each sentence can be only marked as concurrent or not, while in theory the data allows you to see which exact charge it can be served concurrently with.

## Notes

- Wisconsin court case numbers are composed of a year, case type, and number. CF is felony and CM is misdemeanor
- Case numbers count up sequentially from 1. We use this to know when we are done, although this is not necessarily guaranteed, so check after the script says you are done using the case search. It's usually pretty good, but not guaranteed to be perfect
- Wisconsin court case numbers are not unique. Each county will record a case for most case numbers. So for example case 2022CF000001 exists for all 72 counties. The only unique representation is the (case number, county) pair