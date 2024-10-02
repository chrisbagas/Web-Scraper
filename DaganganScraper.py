import re
import time
import numpy as np
import pandas as pd
from appium import webdriver
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime


class DaganganData:

    def __init__(self, version, adb_name, locations, targets):
        self.location = locations
        self.targets = targets
        self.result = None
        self.version = version
        self.adb_name = adb_name
        self.driver = self.initialize_driver()
        self.wait = WebDriverWait(self.driver, 20)  # Wait for up to 20 seconds

    def initialize_driver(self):
        desired_caps = {
            'platformName': 'Android',
            'deviceName': str(self.adb_name),  # Replace with your device name
            'udid': str(self.adb_name),  # Replace with your device UDID
            # Replace with your Android version (e.g., 11)
            'platformVersion': str(self.version),
            'appPackage': 'com.dagangan.mall',
            'appActivity': 'com.dagangan.MainActivity',
            'automationName': 'UiAutomator2',  # Use UiAutomator2 for Android
            'noReset': True,  # Keeps the app data between sessions
            'newCommandTimeout': 6000,  # Timeout for new commands to the server
            # Timeout for ADB commands (adjust as needed)
            'adbExecTimeout': 20000,
            'autoGrantPermissions': True,  # Grant necessary permissions automatically
            # Disable window animations for faster test execution
            'disableWindowAnimation': True,
            'unicodeKeyboard': True,  # Enable Unicode input (if needed)
            'resetKeyboard': True,  # Reset keyboard after test (if needed)
            "appium:ensureWebviewsHavePages": True
        }
        options = UiAutomator2Options().load_capabilities(caps=desired_caps)
        return webdriver.Remote('http://127.0.0.1:4723', options=options)

    def extractor(self):

        self.products = {location: {} for location in self.location}
        for location in self.location:
            print('location: ', location)
            time.sleep(6)
            search_bar = self.wait.until(
                EC.visibility_of_element_located((By.XPATH, '//android.widget.EditText[@resource-id="text-input"]')))

            search_bar.click()
            for target in self.targets:
                retry = True
                while retry:
                    try:
                        time.sleep(2)

                        # Find the search text element
                        search_text = self.wait.until(EC.visibility_of_element_located(
                            (By.CLASS_NAME, 'android.widget.EditText')))
                        search_text.send_keys(target)
                        time.sleep(2)
                        search_text.click()

                        self.driver.press_keycode(66)
                        time.sleep(4)
                        # Try to scrape and update products
                        try:
                            self.products[location].update(self.scrape())
                        except Exception as e:
                            print(
                                f"Scraping error for target {target} in location {location}: {e}")
                            raise  # Raise exception to trigger retry of the entire block

                        # Go back after processing each target
                        self.driver.back()
                        clear_search = self.wait.until(EC.visibility_of_element_located(
                            (By.XPATH, '//android.view.ViewGroup[@content-desc="icon-ic_clear"]')))
                        clear_search.click()
                        retry = False
                    except Exception as e:
                        time.sleep(2)

                        if (self.driver.find_elements(By.XPATH, '//android.widget.EditText[@resource-id="text-input"]')):
                            search_bar = self.wait.until(
                                EC.visibility_of_element_located((By.XPATH, '//android.widget.EditText[@resource-id="text-input"]')))
                            search_bar.click()

                        # If an exception occurs, print it and retry the entire block
                        print(
                            f"Error encountered while processing targets for location {location}: {e}. Retrying...")
                        retry = True
            # Go back after processing all targets
            self.driver.back()
            self.dataframe()
        self.driver.quit()

    def scrape(self):

        # Initialize an empty list to store the products as dictionaries
        products = {}
        counter = 2
        try:
            while True:
                view_group = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                               '//android.widget.ScrollView/android.view.ViewGroup')))

                product_views = view_group.find_elements(
                    By.XPATH, value="./android.view.ViewGroup")
                # Temporary variables to store product info while iterating
                product_name = None
                product_prices = []  # To store the different price options
                product_added = False

                # Iterate through each TextView and process text
                for title_view in product_views:
                    texts = title_view.find_elements(
                        by='class name', value='android.widget.TextView')
                    for text in texts:
                        text = text.get_attribute('text')
                        if 'Rp' in text and product_name is not None:  # Indicates it's a price, and name was found
                            price_parts = text.strip().replace('.', '').split('Rp')
                            for price_part in price_parts:
                                # Extract the price and unit (e.g., /PCS or /CTN)
                                if len(price_part) > 1:
                                    # print(price_part)
                                    price_text = price_part
                                    unit = ''
                                    if ('/' in price_part):
                                        price_text = price_text.split(
                                            '/')[0]
                                    price_text = price_text[:-1]
                                    try:
                                        price = int(price_text)
                                        # print(price)
                                        # print('------------------')
                                    except ValueError:
                                        price = None

                                    if 'karton' in text or 'isi' in text:
                                        # Extract the quantity and divide the price
                                        try:
                                            quantity = int(
                                                text.split('isi')[1].strip().strip(')'))
                                            price_per_unit = price // quantity if price and quantity > 0 else price
                                        except (IndexError, ValueError):
                                            print(
                                                f"Error extracting quantity for {product_name}: {text}")
                                            price_per_unit = price
                                    else:
                                        price_per_unit = price  # Standard case with /PCS

                                    if price_per_unit:
                                        # Add the price for comparison
                                        product_prices.append(
                                            price_per_unit)

                        elif 'BELI' in text:  # Indicate that this is the last price
                            # Finalize the product
                            if product_name and product_prices:  # Indicates a new product is found
                                product_max_price = max(product_prices)
                                product_min_price = min(product_prices)
                                if product_name not in products:
                                    products[product_name] = {
                                        'max_price': product_max_price,
                                        'min_price': product_min_price,
                                        # 'prices': product_prices
                                    }
                                    product_added = True
                                    counter = 2
                                else:
                                    if product_max_price > products[product_name]['max_price']:
                                        products[product_name]['max_price'] = product_max_price
                                        product_added = True
                                        counter = 2
                                    if product_min_price < products[product_name]['min_price']:
                                        products[product_name]['min_price'] = product_min_price
                                        product_added = True
                                        counter = 2
                            # Reset for the next product
                            product_prices = []
                        elif ('promo' not in text.lower() and 'min' not in text and
                              'rekomendasi' not in text.lower() and 'beli' not in text.lower()
                              and 'Rp' not in text and 'ingatkan' not in text.lower() and
                              'stok' not in text.lower()):
                            product_name = text
                            product_prices = []

                if product_name and product_prices:  # Save the last found product if any
                    product_max_price = max(product_prices)
                    product_min_price = min(product_prices)
                    if product_name not in products:
                        products[product_name] = {
                            'max_price': product_max_price,
                            'min_price': product_min_price,
                            # 'prices': product_prices
                        }
                        product_added = True
                        counter = 2

                scroll = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                           '//android.widget.ScrollView')))
                if product_added:
                    self.driver.execute_script("gesture: swipe", {
                        'elementId': scroll.id,
                        "percentage": 100,
                        "direction": "up"})
                else:
                    counter -= 1
                    product_added = True
                    self.driver.execute_script("gesture: swipe", {
                        'elementId': scroll.id,
                        "percentage": 100,
                        "direction": "up"})
                    time.sleep(2)
                    if counter == 0:
                        break
                product_added = False
        except Exception as e:
            print(f"Error encountered while scraping: {e}")
        print(products)
        return products

    def dataframe(self):
        data = []

        # Iterate through the dictionary and extract the needed information
        for location, product_data in self.products.items():
            for product_name, price_data in product_data.items():
                shelf_price = price_data.get('max_price')
                net_price = price_data.get('min_price')
                data.append([product_name, shelf_price, net_price, location])

        # Create DataFrame
        df = pd.DataFrame(data, columns=[
                          'productName', 'basePrice', 'finalPrice', 'location'])

        file_name = f"./dagangan/DAGANGAN_{datetime.now().strftime('%y%m%d')}.xlsx"
        df.to_excel(file_name, index=False)
        self.result = df


targets = ['royco', 'bango', 'sariwangi',
           'pepsodent', 'lifebuoy',
           'rexona', 'clear', 'sunsilk', 'glow',
           'sunlight', 'rinso', 'molto']
locations = ['Jakarta']

dagangan_scrapper = DaganganData('7.1.2', '127.0.0.1:5555', locations, targets)
# dagangan_scrapper.scrape()
dagangan_scrapper.extractor()
print(dagangan_scrapper.result)
