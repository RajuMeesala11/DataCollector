from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

# Set up Chrome options
chrome_options = Options()
# chrome_options.add_argument('--headless')  # Uncomment to run in headless mode

# Initialize the Chrome WebDriver with the new syntax
driver = webdriver.Chrome(
	service=Service(ChromeDriverManager().install()),
	options=chrome_options
)

url = "https://www.datacenters.com/locations?query=USA"
driver.get(url)

time.sleep(10)
# Use XPath to locate elements
# elements = driver.find_elements(By.XPATH, "//div[contains(@class,'LocationTile__detailsContainer')]/div/div[3]")
# for element in elements:
#     print(element.text.strip())
driver.find_element(By.XPATH, "//input[@id='locations-search']").send_keys("United States")
time.sleep(5)
while True:
	time.sleep(5)
	item = driver.find_element(By.XPATH, "(//div[contains(@class,'LocationsIndex__pagination')][1]/div/nav/button/div[contains(text(),'➞')])[2]").is_enabled()
	time.sleep(5)
	elements=driver.find_elements(By.XPATH, "//div[contains(@class,'LocationTile__details__')]")
	original_tab = driver.current_window_handle
	for element in elements:
		element.click()
		time.sleep(5)
		new_tab = [tab for tab in driver.window_handles if tab != original_tab][0]
		if new_tab in driver.window_handles:
			driver.switch_to.window(new_tab)
			summary = driver.find_element(By.XPATH, "//div[contains(@class,'LocationShowMainContent__contentSummary')]").text
			driver.close()
		driver.switch_to.window(original_tab)
		time.sleep(5)
		with open('datacentersSumm1.csv', mode='a', newline='') as file:
			pd.DataFrame({
				'Summary': [summary]
			}).to_csv(file, header=False, index=False)
	time.sleep(5)
	driver.switch_to.window(original_tab)
	driver.find_element(By.XPATH, "(//div[contains(@class,'LocationsIndex__pagination')][1]/div/nav/button/div[contains(text(),'➞')])[2]").click()
	if item == False:
		break

driver.quit()