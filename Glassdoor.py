from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import csv
LEMONADE_DATA = r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\LemonadeDbPlay.csv'
COLUMN_NAMES = ['Company Name', 'Ticker', 'Location', 'Location Type', 'Sales', 'SIC', 'URL', 'Phone Number', '', 'Category', 'CompanySize']
OUTPUT_CSV = r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\output.csv'
CHROMEDRIVER_LOCATION = '/Users/jacob/chromedriver'
EMAIL = 'jacoballenwest@gmail.com'
PASSWORD = "orem2007"

class GlassdoorScraping:

    def __init__(self):
        self.driver = webdriver.Chrome(CHROMEDRIVER_LOCATION)

    def getCompanySize(self, row):
        return 10

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

    def start(self):

        self.logIntoGlassdoor()

        # Open the CSV and read the rows
        with open(LEMONADE_DATA, newline='') as csvfile:

            reader = csv.reader(csvfile)
            data = []
            df = pd.DataFrame(columns=COLUMN_NAMES)  # creates master dataframe
            isTheHeader = True

            for row in reader:
                if not isTheHeader:
                    # We are now working with a company row inside of the data sheet
                    companySize = self.getCompanySize(row)
                    row.append(companySize)
                    data.append(row)
                else:
                    isTheHeader = False

        temp_df = pd.DataFrame(data, columns=COLUMN_NAMES)
        df = df.append(temp_df)

        self.writeToCsv(df)
        self.driver.close() # Close the web driver

scraper = GlassdoorScraping()
scraper.start()