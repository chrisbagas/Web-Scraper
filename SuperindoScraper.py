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


class SuperindoData:

    def __init__(self, version, adb_name, locations, targets):
        self.location = locations
        self.targets = targets
        self.result = None
        self.version = version
        self.adb_name = adb_name
        self.driver = self.initialize_driver()
        self.wait = WebDriverWait(self.driver, 10)  # Wait for up to 20 seconds

    def initialize_driver(self):
        desired_caps = {
            'platformName': 'Android',
            'deviceName': str(self.adb_name),  # Replace with your device name
            'udid': str(self.adb_name),  # Replace with your device UDID
            # Replace with your Android version (e.g., 11)
            'platformVersion': str(self.version),
            'appPackage': 'id.co.superindo.mysuperindo',
            'appActivity': 'id.co.superindo.mysuperindo.MainActivity',
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
            "appium:ensureWebviewsHavePages": True,
            'autoLaunch': True
        }
        options = UiAutomator2Options().load_capabilities(caps=desired_caps)
        driver = webdriver.Remote('http://127.0.0.1:4723', options=options)

        # Bring the app to the foreground (activate app)
        driver.activate_app('id.co.superindo.mysuperindo')

        return driver

    def change_location(self, location):
        # time.sleep(8)

        location_button = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                            '//android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup[1]')))
        location_button.click()
        while True:
            try:
                location_change_button = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                                           '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup[1]')))
                location_change_button.click()
                break
            except:
                location_button = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                                    '//android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup[1]')))
                location_button.click()
                print('Error')
        search_box = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                       '//android.widget.EditText[@text="Cari lokasi (minimal 7 karakter)..."]')))
        search_box.send_keys(location)
        search_box.click()
        time.sleep(2)
        searched_location = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                              '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.widget.ScrollView/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.HorizontalScrollView/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup')))

        searched_location.click()

        change_location_button = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                                   '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[5]')))
        change_location_button.click()

    def check_banner(self):
        # self.driver.back()
        while True:
            try:
                belanja_button = self.wait.until(EC.visibility_of_element_located(
                    (By.XPATH, '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.widget.ImageView[1]')))
                print(belanja_button)
                if belanja_button:
                    print("Banner not detected")
                    break
            except Exception as e:
                print(e)
                print("gagal menemunkan belanja button")
                self.driver.back()
                time.sleep(1)

    def extractor(self, previous_data=None):

        self.products = {location: {} for location in self.location}
        for location in self.location:
            print('location: ', location)
            time.sleep(6)
            self.check_banner()
            belanja_button = self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.widget.ImageView[1]'))).click()
            search_bar = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                          '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.widget.FrameLayout/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View/android.view.View[1]/android.view.View')))

            search_bar.click()
            search_text = self.wait.until(EC.visibility_of_element_located(
                (By.CLASS_NAME, 'android.widget.EditText')))
            for target in self.targets:
                retry = True
                while retry:
                    try:
                        time.sleep(2)

                        # Find the search text element
                        search_text = self.driver.find_element(
                            By.CLASS_NAME, value='android.widget.EditText')
                        search_text.send_keys(target)
                        search_text.click()

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
                        while True:
                            search_text.click()
                            buttons = self.driver.find_elements(
                                By.CLASS_NAME, 'android.widget.ImageView')
                            if len(buttons) > 2:
                                clear_button = buttons[1]
                                clear_button.click()
                                try:
                                    camera_button = self.driver.find_element(
                                        By.XPATH, '//android.view.View[@content-desc="Arahkan kamera ke barcode produk"]')
                                    if camera_button:
                                        self.driver.back()
                                except:
                                    break

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

                # Get the view group containing all TextViews

                view_group = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                                                                              '//android.widget.ScrollView')))
                # Find all TextView elements within the view group
                text_views = view_group.find_elements(
                    by='class name', value='android.view.View')

                # Temporary variables to store product info while iterating
                product_name = None
                product_price = None  # price after discount
                product_original_price = None  # price before discount
                unit = None
                rp_detected = False
                product_added = False
                # Iterate through each TextView and process text
                for text_view in text_views:
                    texts = text_view.get_attribute(
                        'content-desc').strip().split('\n')
                    if len(texts) > 1:
                        for text in texts:
                            # Indicates it's a price, and name was found
                            if 'Beli' in text:
                                continue
                            if ('Rp' in text and product_name is not None) or rp_detected:
                                if 'Rp' in text:
                                    rp_detected = True
                                    continue
                                text = text.replace(".", "")
                                if product_price is None:  # Detect price after discount
                                    product_price = text
                                    product_original_price = text  # Assume no discount
                                elif int(text) > int(product_original_price):
                                    product_original_price = text
                                rp_detected = False
                            elif 'ml' in text or 'gr' in text or 'kg' in text or 'ltr' in text or "'s" in text:
                                unit = text
                            else:  # Detect product name
                                if product_name and product_price:  # Indicates a new product is found
                                    if product_name not in products:
                                        products[product_name] = [
                                            product_price, product_original_price, unit]
                                        product_added = True
                                        counter = 2
                                text = text.strip().replace(".", "")
                                if ('Rp' not in text and len(text) > 0 and not rp_detected
                                            and 'Member' not in text and 'Harga' not in text
                                        ):
                                    if text.isnumeric():
                                        continue
                                    if (product_name is not None or product_price is not None or
                                            product_original_price is not None):
                                        product_name = product_price = product_original_price = discount_amount = None
                                    product_name = text

                if product_name and product_price:  # Indicates a new product is found
                    if product_name not in products:
                        products[product_name] = [
                            product_price, product_original_price, unit]
                        counter = 2
                    product_name = product_price = product_original_price = None

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
            for product_name, (final_price, base_price, unit) in product_data.items():
                if '365' in product_name:
                    continue
                final_price = float(final_price.replace(
                    "Rp", "").replace(".", "").strip())
                base_price = float(base_price.replace(
                    "Rp", "").replace(".", "").strip())
                data.append([product_name, base_price,
                            final_price, unit, location])

        # Create new DataFrame from the current data
        new_df = pd.DataFrame(
            data, columns=['productName', 'basePrice', 'finalPrice', 'unit', 'location'])

        if previous_data and os.path.exists(previous_data):
            # Load previous data from the file
            previous_data = pd.read_excel(previous_data)

            # Append the new data to the previous DataFrame
            combined_df = pd.concat([previous_data, new_df], ignore_index=True)
            self.result = combined_df
        else:
            # If no previous data, set the new DataFrame as result
            self.result = new_df

        # Save the final DataFrame to an Excel file
        file_name = f"../Superindo/SUPERINDO_{datetime.now().strftime('%y%m%d')}.xlsx"
        self.result.to_excel(file_name, index=False)


# targets = ['clear shampoo', 'sunsilk shampoo', 'lifebuoy', 'tresemme', 'ponds',
#            'glow &', 'vaseline', 'pepsodent pasta gigi',
#            'closeup', 'lifebuoy sabun mandi', 'lux', 'rexona', 'axe', 'molto', 'sunlight',
#            'wipol', 'vixal', 'royco', 'bango kecap', 'sariwangi', 'sarimurni', 'buavita',
#            'head & shoulders', 'pantene shampoo', 'zinc', 'garnier', 'nivea',
#            'marina', 'ciptadent pasta gigi', 'nuvo', 'giv', 'posh',
#            'so klin',  'downy pelembut', 'mama lemon', 'super sol',
#            'yuri porstex', 'masako',
#            'sedaap kecap', 'abc kecap manis', 'sosro teh', 'tong tji', 'teh bendera',
#            'country choice', 'citra', 'super pel', 'rinso']
# locations = ['Jakarta']

# superindo_scrapper = SuperindoData(
#     '7.1.2', '127.0.0.1:5555', locations, targets)
# # superindo_scrapper.scrape()
# superindo_scrapper.extractor()
# print(superindo_scrapper.result)


# toko_button = self.driver.find_element(By.XPATH, '//android.widget.TextView[contains(@text, "Pengiriman dari")]')
# toko_text = toko_button.text.split('dari')[1].split('(')[0].strip()
# self.products[location] = {toko_text: {}}

# 'Bandung', 'Surabaya', 'Semarang', 'Yogyakarta', 'Bali', 'Makassar', 'Medan', 'Palembang'
