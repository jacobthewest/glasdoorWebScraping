from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import csv
import random
from selenium.webdriver.chrome.options import Options

LEMONADE_DATA = r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\LinkedIn\LemonadeDbPlay.csv'
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
LOG_FILE = "VS_log.txt"

START_INDEX_INCLUSIVE = 76788
END_INDEX_EXCLUSIVE = 78788

chrome_options = Options()
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument('--disable-dev-shm-usage')

class LINKEDIN_SCRAPING:
    def __init__(self):
        self.driver = webdriver.Chrome(CHROMEDRIVER_LOCATION, chrome_options=chrome_options)

    # Build the member variable that is an array of dictionaries of LinkedIn accounts
    def loadLinkedInAccounts(self):
        tempDic = {}
        with open(LINKEDIN_ACCOUNTS) as file:
            done = False
            while not done:
                line = file.readline().strip()
                if line == '' and len(self.linkedInAccounts) != NUM_LINKEDIN_ACCOUNTS:
                    # Done with current account, reset the dic after appending it
                    self.linkedInAccounts.append(tempDic)
                    tempDic = {}
                elif line == '': # We've hit the end of the file
                    done = True
                else: # We have an account item to add to our temp dictionary
                    tempArr = line.split(': ')
                    tempDic[tempArr[0]] = tempArr[1]

    def buildLinkedInAccountList(self):
        self.linkedInAccounts = []
        self.loadLinkedInAccounts()

    def pickRandomLinkedInAccount(self):
        self.buildLinkedInAccountList()
        # Pick random account from indices 0-5 (inclusive for both)
        randInt = random.randint(0, NUM_LINKEDIN_ACCOUNTS - 1) # -1 because it is inclusive of the final int
        randomLinkedInAccount = self.linkedInAccounts[randInt]
        return randomLinkedInAccount


    def writeToCsv(self, df, includeHeader=False):
        df.to_csv (OUTPUT_CSV, mode='a', index = False, header=includeHeader)

    def logIntoLinkedIn(self):
        self.driver.get('https://www.linkedin.com/') # Navigate to page login

        # Get random LinkedIn login account
        linkedInAccount = self.pickRandomLinkedInAccount()
        email = linkedInAccount[EMAIL_NAME]
        password = linkedInAccount[LINKEDIN_PASSWORD_NAME]

        # Enter Login Information
        self.driver.find_element_by_id('session_key').send_keys(email)
        self.driver.find_element_by_id('session_password').send_keys(password)

        # Login
        loginContainer = self.driver.find_element_by_class_name('sign-in-form-container')

        allButtons = loginContainer.find_elements_by_xpath('//button')
        for button in allButtons:
            print(button.text)
            if button.text == "Sign in":
                button.click()
                break

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

    def navigateToCompanySearch(self):
        searchDiv = self.driver.find_element_by_id('ember18').click() # Find the search bar
        searchDiv.find_element_by_xpath('//input').send_keys("Google") # Put Google into the search bar
        searchDiv.find_element_by_xpath('//input').send_keys(Keys.ENTER) # Run the search
        self.driver.find_element_by_id('ember1670').click() # Click the company filter

    def putCompanyNameIntoSearch(self, companyName):
        searchDiv = self.driver.find_element_by_id('ember18').click() # Find the search bar
        searchInput = searchDiv.find_element_by_xpath('//input') # Focus on the search input

        # Clear the search bar
        while not searchInput.get_attribute("value") == "":
            searchInput.send_keys(Keys.BACK_SPACE)

        searchInput.send_keys("Google")  # Put the company name into the search bar

    def putLocationIntoSearch(self, companyLocation):
        # Click the location filter
        self.driver.find_element_by_id('ember2457').click()

        # Clear previously selected locations (if any)
        selectedLocationsList = self.driver.find_elements_by_class_name('search-reusables__collection-values-item')
        if not selectedLocationsList:
            for selectedItem in selectedLocationsList:
                input = selectedItem.find_element_by_xpath('//input')
                if input.is_selected():
                    input.click() # Clear the selected checkbox

        # Enter location
        div = self.driver.find_element_by_id('ember2461') # Select location div
        input = div.find_element_by_xpath('//input') # Select the input
        input.click().send_keys(companyLocation) # Enter the company location
        input.send_keys(Keys.ARROW_DOWN).send_keys(Keys.ENTER) # Location has been selected now

    def makeSearch(self):
        locationPopout = self.driver.find_element_by_id('artdeco-hoverable-artdeco-gen-44') # Make sure the popout location search is there
        allButtons = locationPopout.find_elements_by_xpath('//buttons')
        for button in allButtons:
            if button.text == "Show results":
                button.click()
                break

    # Returns true if the company name and location are found in the search results.
    # Also returns a clickable link to get to the company page
    def filterSearchResults(self, companyName, location):
        resultTiles = self.driver.find_elements_by_class_name('reusable-search__result-container')
        for result in resultTiles:
            validationArea = result.find_element_by_class_name('mb1')
            nameSpan = validationArea.find_elements_by_class_name('entity-result__title-text')
            # Compare names for a match
            if nameSpan.text.lower() in companyName.lower():
                return True, nameSpan
        return False, None

    # Pulls all of the data that I care about from the company page
    def extractCompanyData(self):
        'LinkedInCompanySize', 'LinkedInIndustry', 'LikedInCompanyPageURL',
        'PeopleWhoWorkAtTheCompanyURL', 'CompanySpecialties', 'MailingLocations'

    def start(self):
        batchSize = 20 # Batch size
        tempProcessed = 0
        self.totalProcessed = 0
        self.logIntoLinkedIn()
        self.navigateToCompanySearch()

        # Open the CSV and read the rows
        with open(LEMONADE_DATA, newline='') as csvfile:
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

                        # Enter company name into the search bar and clear previously entered company name
                        self.putCompanyNameIntoSearch(companyName)

                        # Enter company location into the search and clear previous selected locations
                        self.putLocationIntoSearch(location)

                        # Search the company
                        self.makeSearch()

                        # Filter search results
                        companyExists, linkToCompanyPage = self.filterSearchResults(companyName, location)

                        # Handle the company results
                        if not companyExists:
                            # Set -1 values for all of the columns we want
                            linkedInCompanySize = -1
                            linkedInIndustry = -1
                            linkedInCompanyPageURL = -1
                            peopleWhoWorkAtTheCompanyURL = -1
                            companySpecialties = -1
                            mailingLocations = -1
                        else:
                            # Click into the company page and extract company data
                            linkToCompanyPage.click() # Enter into the company page
                            extractedResults = self.extractCompanyData()

                        row.append(companySize)
                        row.append(industry)
                        data.append(row)
                        tempProcessed += 1
                        self.totalProcessed += 1
                    except Exception as e:
                        print(e)
                        self.logFile.write("--------------------ERROR START--------------------\n")
                        self.logFile.write(row + "\n")
                        self.logFile.write("Error message: " + str(e) + "\n")
                        self.logFile.write("--------------------ERROR END--------------------\n")
                        self.logFile.close()
                        self.driver.close() # Close the web driver
                        exit(-1)
                else:
                    isTheHeader = False
            df, data, printHeader, tempProcessed = self.processBatch(df, data, printHeader)
        self.driver.close() # Close the web driver
        self.logFile.close()

scraper = LINKEDIN_SCRAPING()
scraper.start()
# start = time.time()
# scraper.start()
# end = time.time()
# print("Time elapsed: " + str(end - start) + ", Records written: " + str(scraper.totalProcessed))