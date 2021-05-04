from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import csv
LEMONADE_DATA = r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\LemonadeDbPlay.csv'

# Get company name and location
# Write fake company size to list


# Open the CSV and read the rows
with open(LEMONADE_DATA, newline='') as csvfile:
    df = None
    rowsProcessed = 0
    reader = csv.reader(csvfile)
    data = []
    columnNames = None
    for row in reader:
        if rowsProcessed == 0:
            row.append('New Column Jacob!')
            columnNames = row
            df = pd.DataFrame(columns=row)  # creates master dataframe
        elif rowsProcessed < 10:
            row.append("Please Work")
            data.append(row)
        rowsProcessed += 1
temp_df = pd.DataFrame(data, columns=columnNames)
df = df.append(temp_df)

df.to_csv (r'C:\Users\jacob\Documents\Sprummer2021\LemonadeStand\webScraping\output.csv', index = False, header=True)
