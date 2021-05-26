from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import csv
import random
from selenium.webdriver.chrome.options import Options
from fuzzywuzzy import fuzz

LEMONADE_DATA = r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\LemonadeDbPlay.csv'
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

START_INDEX_INCLUSIVE = 1
END_INDEX_EXCLUSIVE = 3

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
        searchDiv = self.driver.find_element_by_id('global-nav-typeahead') # Find the search bar
        searchDiv.click()
        searchDiv.find_element_by_xpath('//input').send_keys("Google") # Put Google into the search bar
        searchDiv.find_element_by_xpath('//input').send_keys(Keys.ENTER) # Run the search
        time.sleep(2)
        allButtons = self.driver.find_elements_by_xpath('//button')
        for button in allButtons:
            if button.text == "Companies":
                button.click() # Click the company filter
                break

    def putCompanyNameIntoSearch(self, companyName):

        # Handle LinkedIn Premium popup
        self.removePremiumPopup()

        allInputs = self.driver.find_element_by_xpath('//input')
        searchInput = self.driver.find_element_by_xpath('//input[@aria-label="Search"]')# Find the search bar
        searchInput.click() # Focus on the search input

        # Clear the search bar
        while not searchInput.get_attribute("value") == "":
            searchInput.send_keys(Keys.BACK_SPACE)

        searchInput.send_keys(companyName)  # Put the company name into the search bar
        searchInput.send_keys(Keys.ENTER) # Click out of the search bar

    def filterSearchByLocation(self, companyLocation):
        # Click the location filter
        buttonCarousel = self.driver.find_element_by_class_name('peek-carousel__slides')

        allButtons = buttonCarousel.find_elements_by_xpath('//button')
        for button in allButtons:
            if button.text == "Locations":
                button.click()
                break

        # Clear previously selected locations (if any)
        selectedLocationsList = self.driver.find_elements_by_class_name('search-reusables__collection-values-item')
        if selectedLocationsList:
            for selectedItem in selectedLocationsList:
                input = selectedItem.find_element_by_xpath('//input')
                if input.is_selected():
                    input.click() # Clear the selected checkbox

        time.sleep(1)

        # Enter location
        input = self.driver.find_element_by_xpath('//input[@aria-label="Add a location"]') # Select location div
        input.click()
        input.send_keys(companyLocation) # Enter the company location
        locations = self.driver.find_elements_by_xpath('//span')
        for loc in locations:
            if ", United States" in loc.text:
                location = loc
                break
        location.click() # Location has been selected now

    def makeSearch(self):
        allButtons = self.driver.find_elements_by_xpath('//span')
        for button in allButtons:
            if button.text == "Show results":
                button.click()
                break

    # Returns true if the company name and location are found in the search results.
    # Also returns a clickable link to get to the company page
    # TODO: pickup here
    def filterSearchResults(self, companyName, location):
        main = self.driver.find_element_by_id('main')
        allAs = main.find_elements_by_xpath('//a')
        for companyLink in allAs:
            tempName = companyLink.text
            # Compare names for a match
            print(fuzz.token_set_ratio(tempName, companyName))
            if fuzz.token_set_ratio(tempName, companyName) > 50:
                return True, companyLink
        return False, None

    def getURLs(self):
        companypageURL = self.driver.current_url
        employeesURL = companypageURL + 'people/'
        return companypageURL, employeesURL

    def getMailingLocation(self):
        locationsList = self.driver.find_element_by_id('ember395').find_element_by_xpath('//ul')
        primaryLocation = locationsList.find_element_by_xpath('//li[1]')
        pTag = primaryLocation.find_element_by_xpath('//p')
        mailingLocation = pTag.text
        return mailingLocation

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
        # Click the about page
        self.driver.find_element_by_id('ember2078').click()

        # Pull about page data
        dataTable = self.driver.find_element_by_xpath('//dl')
        labels = dataTable.find_elements_by_xpath('//dt')
        values = dataTable.find_elements_by_xpath('//dd')

        # Clean up the values really quick
        values = self.cleanAboutValues(values)

        for i in range(len(labels)):
            if labels[i].text == 'Industry':
                industry = values[i].text
            elif labels[i].text == 'CompanySize':
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

    def removePremiumPopup(self):
        try:
            backToLinkedInButton = self.driver.find_element_by_xpath('//a[@data-control-name="chooser-back-to-linkedin"]')
            backToLinkedInButton.click()
        except:
            pass

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

                        time.sleep(1)

                        # Enter company location into the search and clear previous selected locations
                        self.filterSearchByLocation(location)

                        # Search the company
                        self.makeSearch()

                        # Filter search results
                        companyExists, linkToCompanyPage = self.filterSearchResults(companyName, location)

                        # Handle the company results
                        if not companyExists:
                            # Set -1 values for all of the columns we want
                            extractedResults = [-1, -1, -1, -1, -1, -1]
                        else:
                            # Click into the company page and extract company data
                            linkToCompanyPage.click() # Enter into the company page
                            #extractedResults = '[LinkedInCompanySize', 'LinkedInIndustry', 'LinkedInCompanyPageURL','PeopleWhoWorkAtTheCompanyURL', 'CompanySpecialties', 'MailingLocations']
                            extractedResults = self.extractCompanyData()

                        row = row + extractedResults
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
start = time.time()
scraper.start()
end = time.time()
print("Time elapsed: " + str(end - start) + ", Records written: " + str(scraper.totalProcessed))