from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import csv
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

LEMONADE_DATA = r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\LemonadeDbPlay.csv'
COLUMN_NAMES = ['Company Name', 'Ticker', 'Location', 'Location Type', 'Sales', 'SIC', 'URL', 'Phone Number', '', 'Category', 'GlassdoorCompanySize', 'GlassdoorIndustry']
OUTPUT_CSV = r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\output.csv'
CHROMEDRIVER_LOCATION = '/Users/jacob/chromedriver'
EMAIL = 'jacoballenwest@gmail.com'
PASSWORD = "orem2007"
COMPANY_NAME_INDEX = 0
LOCATION_INDEX = 2
LOG_FILE = "log.txt"

class GlassdoorScraping:

    def __init__(self):
        self.driver = webdriver.Chrome(CHROMEDRIVER_LOCATION)

    def getCompanySizeAndIndustry(self, row):
        try:
            aTag = self.driver.find_element_by_class_name('company-tile')
            companyTileItems = aTag.text.splitlines()

            # TODO: Is this something I want to keep?
            # Handle Aquila Energy Situation
            # if "Employees" in companyTileItems[2]:
            #     industry = -1
            #     companySize = companyTileItems[2]
            # else:
            industry = companyTileItems[2]
            companySize = companyTileItems[3]


            if "US" in companySize:
                companySize = -1
                industry = -1

            return companySize, industry
        except Exception as e:
            companySize = -1
            industry = -1
            return companySize, industry
            # print(e)
            # self.logFile.write("ERROR\n")

    def writeToCsv(self, df, includeHeader=False):
        df.to_csv (OUTPUT_CSV, mode='a', index = False, header=includeHeader)

    def clickFirstSignInButton(self):
        nav = self.driver.find_element_by_id('SiteNav').find_element_by_xpath('//nav')
        thisDiv = nav.find_element_by_class_name('LockedHomeHeaderStyles__fullWidth')
        # thisDiv
        # |  \  \
        # a  div  div
        #    |
        #  button
        allButtons = thisDiv.find_elements_by_xpath('//button')
        for button in allButtons:
            if button.text == "Sign In":
                button.click()
                break

    def clickSecondSignInbutton(self):
        signInForm = self.driver.find_element_by_xpath('//form[@name="emailSignInForm"]')
        buttons = signInForm.find_elements_by_xpath('//button')
        buttons[-1].click() # There are two buttons of each type. Trust that the
                            # second "Sign In" button is the correct button :)
        self.driver.implicitly_wait(5) # Wait 5 seconds for the logged in page to load.

    def logIntoGlassdoor(self):
        self.driver.get('https://www.glassdoor.com/index.htm')
        self.clickFirstSignInButton()
        self.driver.find_element_by_xpath('//input[@id="userEmail"]').send_keys(EMAIL)
        self.driver.find_element_by_xpath('//input[@id="userPassword"]').send_keys(PASSWORD)
        self.clickSecondSignInbutton()

    # Remove "INC.", "LLC", "commas", "Company", and "(Inc)"
    def cleanCompanyName(self, companyName):
        companyName = companyName.replace('INCORPORATED', '')
        companyName = companyName.replace('(INC)', '')
        companyName = companyName.replace('INC.', '')
        companyName = companyName.replace('INC', '')
        companyName = companyName.replace('LLC', '')
        companyName = companyName.replace(',', '')
        companyName = companyName.replace('Company', '')

        return companyName

    def cleanCompanyLocation(self, companyLocation):
        companyLocation = companyLocation.replace('USA', '')
        companyLocation = companyLocation.replace('(USA)', '')
        companyLocation = companyLocation.replace('()', '')
        return companyLocation

    def clearCompany(self):
        self.driver.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'r')
        try:
            element = self.driver.find_element_by_id("sc.keyword")
            while not element.get_attribute("value") == "":
                element.send_keys(Keys.BACK_SPACE)
        except Exception as e:
            print(e)
            self.logFile.write("ERROR\n")

    def clearLocation(self):
        try:
            element = self.driver.find_element_by_id("sc.location")
            while not element.get_attribute("value") == "":
                element.send_keys(Keys.BACK_SPACE)
        except Exception as e:
            print(e)
            self.logFile.write("ERROR\n")

    def clearSearch(self):
        self.clearCompany()
        self.clearLocation()


    def locateCompanyPage(self, companyName, companyLocation):
        try:
            companyName = self.cleanCompanyName(companyName)
            companyLocation = self.cleanCompanyLocation(companyLocation)

            self.driver.find_element_by_id("sc.keyword").send_keys(companyName) # Fill in the company name
            self.driver.find_element_by_class_name("universalSearch__UniversalSearchBarStyles__searchInputContainer").click() # Click the location search area
            self.driver.find_element_by_id("sc.location").send_keys(companyLocation) # Put in the company location
            self.driver.find_element_by_xpath('//button[@title="Search Submit"]').click()
            time.sleep(5)
        except Exception as e:
            print(e)
            self.logFile.write("ERROR\n")

    def refreshPage(self):
        self.driver.get('https://www.glassdoor.com/index.htm')

    def processBatch(self, df, data, printHeader, totalProcessed):
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
            rowNumInOutputCSV = totalProcessed - len(df.values) + i + 1
            self.logFile.write('[' + str(rowNumInOutputCSV) + '] ' + companyName + "\n")
        data = []  # Empty data
        df = df[0:0].copy()  # Empty the dataframe, but keep the column information
        tempProcessed = 0
        return df, data, printHeader, tempProcessed

    def start(self):
        batchSize = 2 # Batch size
        tempProcessed = 0
        totalProcessed = 0
        self.logIntoGlassdoor()

        # Open the CSV and read the rows
        with open(LEMONADE_DATA, newline='') as csvfile:
            self.logFile = open(LOG_FILE, "w")
            reader = csv.reader(csvfile)
            data = []
            df = pd.DataFrame(columns=COLUMN_NAMES)  # creates master dataframe
            isTheHeader = True
            printHeader = True

            for row in reader:
                if tempProcessed == batchSize:
                    df, data, printHeader, tempProcessed = self.processBatch(df, data, printHeader, totalProcessed)
                if not isTheHeader:
                    try:
                        # We are now working with a company row inside of the data sheet
                        companyName = row[COMPANY_NAME_INDEX]
                        location = row[LOCATION_INDEX]
                        self.clearSearch()
                        self.locateCompanyPage(companyName, location)
                        companySize, industry = self.getCompanySizeAndIndustry(row)
                        self.refreshPage()
                        row.append(companySize)
                        row.append(industry)
                        data.append(row)
                        tempProcessed += 1
                        totalProcessed += 1
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
            df, data, printHeader, tempProcessed = self.processBatch(df, data, printHeader, totalProcessed)
        self.driver.close() # Close the web driver

scraper = GlassdoorScraping()
scraper.start()