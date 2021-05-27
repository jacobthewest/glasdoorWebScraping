from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import csv
import random
from selenium.webdriver.chrome.options import Options
from fuzzywuzzy import fuzz

LEMONADE_DATA = r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\outputPlay.csv'
COLUMN_NAMES = ['Company Name', 'Ticker', 'Location', 'Location Type', 'Sales', 'SIC', 'URL', 'Phone Number', '', 'Category',
                'GlassdoorCompanySize', 'GlassdoorIndustry', 'LinkedInCompanySize', 'LinkedInIndustry', 'LinkedInCompanyPageURL',
                'PeopleWhoWorkAtTheCompanyURL', 'CompanySpecialties', 'MailingLocations']
OUTPUT_CSV = r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\LinkedIn\linkedInOutput_pycharm.csv'
CHROMEDRIVER_LOCATION = '/Users/jacob/chromedriver'
LINKEDIN_ACCOUNTS = r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\LinkedIn\resources\LinkedInAccounts'
COMPANY_NAME_INDEX = 0
LOCATION_INDEX = 2
EMAIL_NAME = 'Email'
LINKEDIN_PASSWORD_NAME = 'LinkedInPassword'
NUM_LINKEDIN_ACCOUNTS = 6
LOG_FILE = "pycharm_log.txt"

START_INDEX_INCLUSIVE = 0
END_INDEX_EXCLUSIVE = 10

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-dev-shm-usage')

class LINKEDIN_SCRAPING:
    def __init__(self):
        self.driver = webdriver.Chrome(CHROMEDRIVER_LOCATION, chrome_options=chrome_options)

    def writeToCsv(self, df, includeHeader=False):
        df.to_csv (OUTPUT_CSV, mode='a', index = False, header=includeHeader)

    def processBatch(self, df, data, printHeader):
        temp_df = pd.DataFrame(data, columns=COLUMN_NAMES)
        df = df.append(temp_df)

        if printHeader == True:
            self.writeToCsv(df, True)
            printHeader = False
        else:
            self.writeToCsv(df)

        for i in range(len(df.values)):
            companyName = df.values[i][0]

            # Row number in output csv
            rowNumInOutputCSV = self.totalProcessed - len(df.values) + i + 1
            self.logFile.write('[' + str(rowNumInOutputCSV) + '] ' + companyName + "\n")
            print('[' + str(rowNumInOutputCSV) + '] ' + companyName + "\n")

        data = []  # Empty data
        df = df[0:0].copy()  # Empty the dataframe, but keep the column information
        tempProcessed = 0
        return df, data, printHeader, tempProcessed

    def getURLs(self):
        time.sleep(1)
        companypageURL = self.driver.current_url

        # Clean up the url for the employeeURL
        trimmedURL = companypageURL.replace('about/','')

        if trimmedURL[-1] != '/':
            trimmedURL = trimmedURL + '/'

        employeesURL = trimmedURL + 'people/'
        return companypageURL, employeesURL

    def getMailingLocation(self):
        try:
            # Get the locations part of the page
            containsSelector = '[contains(@class,"locations") and contains(@class, "section-container")]'
            locationsListSpans = self.driver.find_elements_by_xpath('//section' + containsSelector + '/ul/li/span')

            # Process all spans and pick the Primary address span and get its index for future xPath stuff with li elements
            listItemIndexWithPrimaryAdddress = 1 # Default to one in case there is an address w/o a primary address
            i = 1
            for span in locationsListSpans:
                if span.text == "Primary":
                    listItemIndexWithPrimaryAdddress = i
                    break
                else:
                    i += 1

            # Get the first part of the address
            liSelector = "[" + str(listItemIndexWithPrimaryAdddress) + "]"
            ps = self.driver.find_elements_by_xpath('//section' + containsSelector + '/ul/li' + liSelector + '/p')
            fullAddress = ''
            for p in ps:
                fullAddress = fullAddress + p.text + ' '

            mailingLocation = fullAddress[:len(fullAddress) - 1] # Delete trailing whitespace char
            return mailingLocation

        except Exception as e:
            return -1 # Default value in case no mailing location exists

    # Removes a stat that says how many company employees are on LinkedIn
    def cleanAboutValues(self, values):
        delIndex = -1
        for i in range(len(values)):
            if "on LinkedIn" in values[i].text:
                delIndex = i
                break
        if delIndex >= 0:
            del values[delIndex]
        return values

    def getAboutInfo(self):

        # Pull page data
        dataTable = self.driver.find_element_by_xpath('//dl')
        labels = dataTable.find_elements_by_xpath('//dt')
        values = dataTable.find_elements_by_xpath('//dd')

        # Clean up the values really quick
        values = self.cleanAboutValues(values)

        industry = -1
        companySize = -1
        specialties = -1

        for i in range(len(labels)):
            if labels[i].text == 'Industries':
                industry = values[i].text
            elif labels[i].text == 'Company size':
                companySize = values[i].text
            elif labels[i].text == 'Specialties':
                specialties = values[i].text

        mailingLocation = self.getMailingLocation()
        return companySize, industry, specialties, mailingLocation

    # Pulls all of the data that I care about from the company page
    def extractCompanyData(self):
        companyPageURL, employeesURL = self.getURLs()
        companySize, industry, specialties, mailingLocation = self.getAboutInfo()

        returnDic = {}
        returnDic['LinkedInCompanySize'] = companySize
        returnDic['LinkedInIndustry'] = industry
        returnDic['LikedInCompanyPageURL'] = companyPageURL
        returnDic['PeopleWhoWorkAtTheCompanyURL'] = employeesURL
        returnDic['CompanySpecialties'] = specialties
        returnDic['MailingLocations'] = mailingLocation
        return returnDic

    def goToGoogle(self):
        self.driver.get('https://www.google.com/')

    def performGoogleSearch(self, companyNameForSearch, locationForSearch):
        searchBar = self.driver.find_element_by_xpath('//input[@aria-label="Search"]')
        searchBar.click()
        searchString = "site:linkedin.com " + companyNameForSearch + " " + locationForSearch
        searchBar.send_keys(searchString)
        searchBar.send_keys(Keys.ENTER)

    # Returns True if result was selected
    # Returns False if no result was found
    def selectAResult(self, companyNameForSearch, locationForSearch):
        resultTitles = self.driver.find_elements_by_xpath('//h3')

        # Formats the title to closer match what a correct search result will appear
        linkedInCompanyNameSearchTitle = companyNameForSearch + " | LinkedIn"

        for result in resultTitles:
            tempTitle = result.text

            # Compare names for a match
            percentMatch = fuzz.token_set_ratio(tempTitle, linkedInCompanyNameSearchTitle)

            # We need to have 90% confidence in our prediction. Follow it only if there is a
            # fantastic match
            if percentMatch > 90:
                result.click()
                return True
                break
            return False

    def start(self):
        batchSize = 20 # Batch size
        tempProcessed = 0
        self.totalProcessed = 0
        self.goToGoogle()

        # Open the CSV and read the rows
        with open(LEMONADE_DATA, newline='', encoding='utf-8') as csvfile:
            self.logFile = open(LOG_FILE, "w")
            reader = csv.reader(csvfile)
            rows = list(reader)
            data = []
            df = pd.DataFrame(columns=COLUMN_NAMES)  # creates master dataframe
            isTheHeader = True
            printHeader = True

            for index in range(START_INDEX_INCLUSIVE, END_INDEX_EXCLUSIVE):
                row = rows[index]
                if tempProcessed == batchSize:
                    df, data, printHeader, tempProcessed = self.processBatch(df, data, printHeader)
                if not isTheHeader:
                    try:
                        # We are now working with a company row inside of the data sheet
                        companyName = row[COMPANY_NAME_INDEX]
                        location = row[LOCATION_INDEX]

                        # Format the location
                        companyNameForSearch = companyName.lower()
                        locationForSearch = location.lower().replace('(usa)','') # Remove (usa) from text

                        self.performGoogleSearch(companyNameForSearch, locationForSearch)
                        #time.sleep(1) # Wait for the query to go through

                        foundAResult = self.selectAResult(companyNameForSearch, locationForSearch)

                        if foundAResult:
                            # extractedResults = '[LinkedInCompanySize', 'LinkedInIndustry', 'LinkedInCompanyPageURL','PeopleWhoWorkAtTheCompanyURL', 'CompanySpecialties', 'MailingLocations']
                            extractedResults = self.extractCompanyData()
                            dictionaryValuesList = list(extractedResults.values()) # Pull dictionary values into a list
                        else:
                            extractedResults = [-1, -1, -1, -1, -1, -1]
                            dictionaryValuesList = extractedResults

                        # Add dictionary values to the row
                        row = row + dictionaryValuesList
                        data.append(row)
                        tempProcessed += 1
                        self.totalProcessed += 1

                        self.goToGoogle()

                    except Exception as e:
                        print(e)
                        self.driver.close() # Close the web driver
                        exit(-1)
                else:
                    isTheHeader = False
            df, data, printHeader, tempProcessed = self.processBatch(df, data, printHeader)
        self.driver.close() # Close the web driver
        self.logFile.close()

scraper = LINKEDIN_SCRAPING()
start = time.time()
scraper.start()
end = time.time()
print("Time elapsed: " + str(end - start) + ", Records written: " + str(scraper.totalProcessed))