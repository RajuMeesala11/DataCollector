from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up Chrome options
chrome_options = Options()


driver = webdriver.Chrome(
	service=Service(ChromeDriverManager().install()),
	options=chrome_options
)
df = pd.read_csv('datacenters_with_years.csv')  # Replace with your CSV filename
addresses = df['Street Address'].tolist()  # Replace 'street_address' with your column name
url = "https://datacenterhawk.com/marketplace"
driver.get(url)
time.sleep(10)
# Accept cookies if the button is present
try:
    driver.find_element(By.XPATH, "//button[contains(text(),'Accept')]").click()
    time.sleep(5)
except Exception as e:
    print("No cookies acceptance button found or an error occurred:", str(e))

driver.find_element(By.XPATH, "(//div[contains(text(),'Unlock Full List')])[1]").click()
time.sleep(20) 



for address in addresses:
    driver.get(url)
    # driver.find_element(By.XPATH, "//div[@class='shrink-0']/a").click()
    time.sleep(5)
    driver.find_element(By.XPATH, "//input[@id='action-search']").send_keys(address)
    time.sleep(5)
    # Find all results and check size
    results = driver.find_elements(By.XPATH, "//a[@id='result0']")
    if len(results) > 0:
        try:
            driver.find_element(By.XPATH, "(//a[@id='result0'])[1]").click()
            time.sleep(5)
            YearBuilt = driver.find_element(By.XPATH, "//div[contains(text(),'Year Built')]/../div[2]").text
            print(f"Year Built: {YearBuilt}")
            time.sleep(5)
            pd.DataFrame({
			    'Address': [address],
			    'Year': [YearBuilt.strip()],
		    }).to_csv('dataMissingYears.csv', mode='a', header=False, index=False)
        except Exception as e:
            print(f"Error processing {address}: {str(e)}")
            continue
    else:
        pd.DataFrame({
			    'Address': [address],
			    'Year': ['Not Available'],
		    }).to_csv('dataMissingYears.csv', mode='a', header=False, index=False)
        print(f"No results found for {address}")
        continue

driver.quit()