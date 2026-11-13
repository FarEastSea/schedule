from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-dev-shm-usage')

chromedriver = "/usr/local/bin/chromedriver" if os.path.exists("/usr/local/bin/chromedriver") else "/usr/bin/chromedriver"
if os.path.exists(chromedriver):
    service = Service(executable_path=chromedriver)
    driver = webdriver.Chrome(options=chrome_options, service=service)
else:
    driver = webdriver.Chrome(options=chrome_options)

driver.get("https://www.baidu.com")
print(driver.title)
driver.quit()
