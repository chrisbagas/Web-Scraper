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


class AksesmuData:

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
            'appPackage': 'com.alfacart.alfamikroapp',
            'appActivity': 'com.alfadigital.alfamikro.fov3.ui.dashboard.DashboardActivity',
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

    def extractor(self, previous_data=None):

        self.products = {location: {} for location in self.location}
        for location in self.location:
            print('location: ', location)
            time.sleep(6)

            for target in self.targets:
                retry = True
                while retry:
                    try:
                        time.sleep(2)
                        search_bar = self.wait.until(EC.visibility_of_element_located((By.ID,
                                                                                       'com.alfacart.alfamikroapp:id/btnSearch')))

                        search_bar.click()
                        # Find the search text element
                        search_text = self.wait.until(EC.visibility_of_element_located(
                            (By.CLASS_NAME, 'android.widget.EditText')))
                        search_text.send_keys(target)
                        time.sleep(2)
                        while True:
                            try:
                                search_text.click()
                                search_text.click()
                                search_text.click()
                                search_text.click()
                                # self.driver.press_keycode(111)

                                # Press the "Enter" key (keycode 66)
                                self.driver.press_keycode(66)
                                suggest_list = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                                                '(//androidx.recyclerview.widget.RecyclerView[@resource-id="com.alfacart.alfamikroapp:id/rvKeywordHint"])[1]')))
                                break
                            except Exception as e:
                                print(f"Couldn't find suggestions")

                        suggest_button = suggest_list.find_elements(
                            By.ID, 'com.alfacart.alfamikroapp:id/btnSearch')
                        suggest_button[0].click()
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
                        if (not self.driver.find_elements(
                                By.CLASS_NAME, value='android.widget.EditText')):
                            self.driver.back()

                        if (self.driver.find_elements(By.ID, value='android:id/alertTitle')):
                            self.driver.find_element(
                                By.ID, value='android:id/button2').click()
                            search_bar = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                                           '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]/android.view.ViewGroup')))
                            search_bar.click()

                        # If an exception occurs, print it and retry the entire block
                        print(
                            f"Error encountered while processing targets for location {location}: {e}. Retrying...")
                        retry = True
            # Go back after processing all targets
            # self.driver.back()
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

                # Get the view group containing all TextViews

                # view_group = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                #                                                                '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[3]/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup[3]/android.view.ViewGroup')))
                # Find all TextView elements within the view group
                card_views = self.driver.find_elements(
                    By.ID, value='com.alfacart.alfamikroapp:id/card_product')

                # Temporary variables to store product info while iterating
                product_name = None
                product_price = '9999999'  # price after discount
                product_original_price = '9999999'  # price before discount
                product_added = False
                # Iterate through each TextView and process text
                for view in card_views:
                    product_name = view.find_elements(
                        By.ID, 'com.alfacart.alfamikroapp:id/text_name')
                    price_views = view.find_elements(
                        By.CLASS_NAME, 'android.widget.LinearLayout')
                    if product_name:
                        product_name = product_name[0].get_attribute('text')
                        for price_view in price_views:
                            pcs_amount = price_view.find_elements(
                                By.ID, 'com.alfacart.alfamikroapp:id/txt_product_pcs')
                            new_price = price_view.find_elements(
                                By.ID, 'com.alfacart.alfamikroapp:id/txt_product_now_price')
                            old_price = price_view.find_elements(
                                By.ID, 'com.alfacart.alfamikroapp:id/txt_product_old_price')
                            pcs_price = price_view.find_elements(
                                By.ID, 'com.alfacart.alfamikroapp:id/tierPricePcs')
                            if pcs_amount:
                                if pcs_amount[0].get_attribute('text') == '1':
                                    if pcs_price:
                                        if old_price:
                                            text = old_price[0].get_attribute(
                                                'text')
                                            product_original_price = text
                                            product_price = text
                                        else:
                                            text = pcs_price[0].get_attribute(
                                                'text')
                                            product_original_price = text
                                            product_price = text
                                    else:
                                        if new_price:
                                            text = new_price[0].get_attribute(
                                                'text')
                                            product_original_price = text
                                            product_price = text
                                else:
                                    if pcs_price:
                                        text = pcs_price[0].get_attribute(
                                            'text')
                                        text = text.replace('.', '').strip()
                                        product_price = product_price.replace(
                                            '.', '').strip()
                                        if int(text) < int(product_price):
                                            product_price = str(text)

                            keranjang = price_view.find_elements(
                                By.ID, 'com.alfacart.alfamikroapp:id/buyBtn')
                            if keranjang:
                                product_price = product_price.replace(
                                    '.', '').strip()
                                # Indicates a new product is found
                                if product_name and int(product_price) < 9999999:
                                    if product_name not in products:
                                        products[product_name] = [
                                            product_price, product_original_price]
                                        product_added = True
                                        counter = 2
                                # Reset for the next product
                                product_name = None
                                product_price = product_original_price = '9999999'
                                pcs_amount = new_price = old_price = pcs_price = keranjang = None

                product_price = product_price.replace('.', '').strip()
                if product_name and int(product_price) < 9999999:
                    if product_name not in products:
                        products[product_name] = [
                            product_price, product_original_price]
                        counter = 2
                product_name = None
                product_price = product_original_price = '9999999'
                pcs_amount = new_price = old_price = pcs_price = keranjang = None

                scroll = self.wait.until(EC.visibility_of_element_located((By.ID,
                                                                           'com.alfacart.alfamikroapp:id/rvProducts')))
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

    def dataframe(self, previous_data=None):
        data = []

        # Iterate through the dictionary and extract the needed information
        for location, product_data in self.products.items():
            for product_name, (final_price, base_price) in product_data.items():
                final_price = float(final_price.replace(
                    "Rp", "").replace(".", "").strip())
                base_price = float(base_price.replace(
                    "Rp", "").replace(".", "").strip())
                data.append([product_name, base_price,
                            final_price, location])

         # Create new DataFrame from the current data
        new_df = pd.DataFrame(data, columns=[
            'productName', 'basePrice', 'finalPrice', 'location'])
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

        file_name = f"../aksesmu/AKSESMU_{datetime.now().strftime('%y%m%d')}.xlsx"
        self.result.to_excel(file_name, index=False)


# targets = ['royco', 'bango', 'sariwangi',
#            'pepsodent white', 'lifebuoy',
#            'rexona', 'clear', 'sunsilk', 'glow lovely',
#            'sunlight', 'rinso molto', 'molto']
# locations = ['Jakarta']

# aksesmu_scrapper = AksesmuData('7.1.2', '127.0.0.1:5555', locations, targets)
# # aksesmu_scrapper.scrape()
# aksesmu_scrapper.extractor()
# print(aksesmu_scrapper.result)
