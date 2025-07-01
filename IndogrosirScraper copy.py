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
import os


class IndogrosirData:

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
            'appPackage': 'com.indogrosir.sd1.myindogrosirGetx',
            'appActivity': 'com.example.superapp.MainActivity',
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

    def change_location(self, location):
        time.sleep(5)
        # scroll = self.wait.until(EC.visibility_of_element_located((By.XPATH,
        #                                                            '//android.widget.ScrollView')))
        # self.driver.execute_script("gesture: swipe", {
        #     'elementId': scroll.id,
        #     "percentage": 100,
        #     "direction": "up"})

        alamat_found = False
        while not alamat_found:
            alamats = self.driver.find_elements(
                By.CLASS_NAME, 'android.view.View')
            for alamat in alamats:
                if location in alamat.get_attribute("content-desc"):
                    if alamat.find_elements(By.CLASS_NAME, 'android.widget.Button'):
                        buttons = alamat.find_elements(
                            By.CLASS_NAME, 'android.widget.Button')
                        for button in buttons:
                            if button.get_attribute("content-desc") == "Pilih Alamat Penerima":
                                button.click()
                                time.sleep(5)
                        alamat_found = True
                        break
            if not alamat_found:
                alamats_scroll = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                                   '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[2]/android.view.View')))
                self.driver.execute_script("gesture: swipe", {
                    'elementId': alamats_scroll.id,
                    "percentage": 100,
                    "direction": "up"})
        if not self.home_checker():
            self.driver.back()

    def check_ad_banner(self):
        if self.driver.find_elements(By.XPATH, value='//android.view.View[@content-desc="Dismiss"]'):
            self.driver.find_element(
                By.XPATH, value='//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View[1]/android.view.View/android.view.View/android.view.View').click()

    def home_checker(self):
        views = self.driver.find_elements(
            By.CLASS_NAME, value='android.view.View')
        home_checker = False
        for view in views:
            if 'Home' in view.get_attribute("content-desc"):
                home_checker = True
                break
        return home_checker

    def extractor(self, previous_data=None):
        time.sleep(15)
        self.check_ad_banner()

        self.products = {location: {} for location in self.location}
        for location in self.location:
            print('location: ', location)
            while True:
                try:
                    self.check_ad_banner()
                    account_tab = self.wait.until(EC.visibility_of_element_located(
                        (By.XPATH, '//android.view.View[@content-desc="Profil"]')))
                    account_tab.click()
                    location_button = self.wait.until(EC.visibility_of_element_located(
                        (By.XPATH, '//android.widget.ImageView[@content-desc="Kelola Alamat"]')))
                    location_button.click()
                    self.change_location(location)
                    self.check_ad_banner()
                    # Check if the location is changed

                except Exception as e:
                    print(f"Error changing location to {location}: {e}")
                    if not self.home_checker():
                        self.driver.back()
            self.check_ad_banner()
            search_bar = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                           '//android.widget.Button[@content-desc="Cari di Klik Indogrosir"]')))
            search_bar.click()
            self.check_ad_banner()
            for target in self.targets:
                retry = True
                while retry:
                    try:
                        time.sleep(2)

                        # Find the search text element
                        search_text = self.driver.find_element(
                            By.CLASS_NAME, value='android.widget.EditText')
                        search_text.click()

                        clear_button = self.driver.find_element(
                            By.XPATH, '//android.widget.EditText/android.widget.Button').click()

                        search_text.send_keys(target)

                        # Press the "Enter" key (keycode 66)
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

                        retry = False
                    except Exception as e:
                        time.sleep(2)
                        home_checker = self.home_checker()
                        if (home_checker):
                            search_bar = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                                           '//android.widget.Button[@content-desc="Cari di Klik Indogrosir"]')))
                            search_bar.click()

                        if (not self.driver.find_elements(
                                By.CLASS_NAME, value='android.widget.EditText') and not home_checker):
                            self.driver.back()

                        # If an exception occurs, print it and retry the entire block
                        print(
                            f"Error encountered while processing targets: {e}. Retrying...")
                        retry = True
            print(self.products)
            # Go back after processing all targets
            self.driver.back()
            if previous_data is None:
                self.dataframe()
        if previous_data is not None:
            self.dataframe(previous_data)
        self.driver.quit()

    def scrape(self):
        # Initialize an empty list to store the products as dictionaries
        products = {}
        counter = 2
        try:
            while True:
                view_group = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                               '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[2]')))

                image_views = view_group.find_elements(
                    by='class name', value='android.widget.ImageView')
                # Temporary variables to store product info while iterating
                product_name = None
                product_prices = []  # To store the different price options
                product_added = False

                # Iterate through each TextView and process text
                for title_view in image_views:
                    if 'Mau' not in title_view.get_attribute(
                            "content-desc"):
                        if '\n' in title_view.get_attribute(
                                "content-desc"):
                            product_name = title_view.get_attribute(
                                "content-desc").split('\n')[1].strip()
                        else:
                            product_name = title_view.get_attribute(
                                "content-desc").strip()
                    if product_name is not None:
                        prices = title_view.find_elements(
                            by='class name', value='android.view.View')
                        for price in prices:
                            try:
                                text = price.get_attribute(
                                    "content-desc").strip()
                            except:
                                continue
                            if 'Rp' in text and product_name is not None:  # Indicates it's a price, and name was found
                                price_parts = text.strip().split('Rp')
                                for price_part in price_parts:
                                    # Extract the price and unit (e.g., /PCS or /CTN)
                                    if len(price_part) > 0:
                                        price_text = price_part.split(
                                            '/')[0].replace('Rp', '').replace('.', '').strip()
                                        try:
                                            price = int(price_text)
                                        except ValueError:
                                            price = None

                                        # Handle cases where there is a quantity (like 12 in a CTN)
                                        if '/CTN' in text or 'isi' in text:
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

                            if 'CTN' in text:  # Indicate that this is the last price
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

                                # Reset for the next product
                                product_name = None
                                product_prices = []

                            # else:  # Detect product name
                            #     if 'Rp' not in text and len(text) > 0:
                            #         if product_name is not None or product_prices:
                            #             product_name = None
                            #             product_prices = []
                            #         product_name = text  # Set the product name

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

                # Scroll for more products
                scroll = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                           '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[2]/android.view.View[1]/android.view.View')))
                if product_added:
                    self.driver.execute_script("gesture: swipe", {
                        'elementId': scroll.id,
                        "percentage": 150,
                        "direction": "up"})
                else:
                    counter -= 1
                    product_added = True
                    self.driver.execute_script("gesture: swipe", {
                        'elementId': scroll.id,
                        "percentage": 150,
                        "direction": "up"})
                    time.sleep(2)
                    print(counter)
                    if counter == 0:
                        print(counter)
                        break
                product_added = False
        except Exception as e:
            print(f"Error encountered while scraping: {e}")
        # print(products)
        return products

    def dataframe(self, previous_data=None):
        data = []

        # Iterate through the dictionary and extract the needed information
        for location, product_data in self.products.items():
            for product_name, price_data in product_data.items():
                shelf_price = price_data.get('max_price')
                net_price = price_data.get('min_price')
                data.append([product_name, shelf_price, net_price, location])
         # Create new DataFrame from the current data
        new_df = pd.DataFrame(data, columns=[
            'productName', 'shelfPrice', 'netPrice', 'location'])
        if previous_data and os.path.exists(previous_data):
            # Load previous data from the file
            previous_data = pd.read_excel(previous_data)
            # Append the new data to the previous DataFrame
            combined_df = pd.concat([previous_data, new_df], ignore_index=True)
            combined_df.drop_duplicates(
                subset=['productName'], keep='first')
            self.result = combined_df
        else:
            # If no previous data, set the new DataFrame as result
            self.result = new_df

        file_name = f"../indogrosir/INDOGROSIR_{datetime.now().strftime('%y%m%d')}.xlsx"
        self.result.to_excel(file_name, index=False)

    def toast(self):
        while True:
            page_source = self.driver.page_source
            print(page_source)
            time.sleep(1)
            print('-----------------------------------------------------------------------------------------------------------------------')


targets = ['royco bumbu pelezat serbaguna', 'bango manis 25g', 'bango manis 77g', 'bango manis 265g',
           'sariwangi asli 1.85g', 'pepsodent white', 'lifebuoy ts', 'lifebuoy 9ml',
           'rexona 9g', 'clear shampoo 9+2', 'sunsilk shampoo 9ml', 'glow lovely 7.5g',
           'sunlight jeruk nipis', 'rinso molto rose fresh', 'molto 10ml']
locations = ['Medan', 'Ciputat', 'Ambon',
             'Makassar', 'Banjarmasin', 'Batam', 'Surabaya']
#
indogrosir_scrapper = IndogrosirData(
    '7.1.2', '127.0.0.1:5555', locations, targets)
# # indogrosir_scrapper.toast()
# # indogrosir_scrapper.scrape()
indogrosir_scrapper.extractor()
# print(indogrosir_scrapper.result)


# toko_button = self.driver.find_element(By.XPATH, '//android.widget.TextView[contains(@text, "Pengiriman dari")]')
# toko_text = toko_button.text.split('dari')[1].split('(')[0].strip()
# self.products[location] = {toko_text: {}}

# 'Bandung', 'Surabaya', 'Semarang', 'Yogyakarta', 'Bali', 'Makassar', 'Medan', 'Palembang'
