from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import csv
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

LEMONADE_DATA = r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\LemonadeDbPlay.csv'
COLUMN_NAMES = ['Company Name', 'Ticker', 'Location', 'Location Type', 'Sales', 'SIC', 'URL', 'Phone Number', '', 'Category', 'CompanySize', 'Industry']
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

    def writeToCsv(self, df):
        df.to_csv (OUTPUT_CSV, index = False, header=True)

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

    def start(self):
        limit = 10
        processed = 0
        self.logIntoGlassdoor()

        # Open the CSV and read the rows
        with open(LEMONADE_DATA, newline='') as csvfile:
            self.logFile = open(LOG_FILE, "w")

            reader = csv.reader(csvfile)
            data = []
            df = pd.DataFrame(columns=COLUMN_NAMES)  # creates master dataframe
            isTheHeader = True

            for row in reader:
                if processed >= limit:
                    break;
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
                        self.logFile.write(companyName + "\n")
                        processed += 1
                    except Exception as e:
                        print(e)
                        self.logFile.write("ERROR\n")
                        self.logFile.close()
                        exit(-1)
                else:
                    isTheHeader = False

        temp_df = pd.DataFrame(data, columns=COLUMN_NAMES)
        df = df.append(temp_df)

        self.writeToCsv(df)
        self.driver.close() # Close the web driver

scraper = GlassdoorScraping()
scraper.start()