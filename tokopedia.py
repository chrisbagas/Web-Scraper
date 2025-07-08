import requests
import pandas as pd
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Retry strategy
retry_strategy = Retry(
    total=10,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
 
def log_request_retry(method, url, retries_left):
    print(f"[Retry] {method} {url} | Retries left: {retries_left}")
 
class VerboseHTTPAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        try:
            return super().send(request, **kwargs)
        except Exception as e:
            log_request_retry(request.method, request.url, self.max_retries.total)
            raise
 
# Use the verbose adapter
http = requests.Session()
verbose_adapter = VerboseHTTPAdapter(max_retries=retry_strategy)
http.mount("https://", verbose_adapter)
http.mount("http://", verbose_adapter)
# DataFrame to store product information
promo_sku = pd.DataFrame(columns=["productName", "basePrice", "finalPrice", "discountPercent"])
 
# Headers for the request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.tokopedia.com/unilever/',
    'X-Tkpd-Lite-Service': 'zeus',
    'X-Version': '1227cf6',
    'content-type': 'application/json',
    'X-Device': 'default_v3',
    'X-Source': 'tokopedia-lite',
    'Origin': 'https://www.tokopedia.com',
    'Connection': 'keep-alive'
}
 
def convert_price(price_str):
    return int(price_str.replace('Rp', '').replace('.', '').strip())
 
def parse_product_card(product_card):
    try:
        # Product name
        name_tag = product_card.find('span', class_='_0T8-iGxMpV6NEsYEhwkqEg==')
        product_name = name_tag.text.strip() if name_tag else ""
 
        # Final price
        final_price_tag = product_card.find('div', class_='_67d6E1xDKIzw+i2D2L0tjw==')
        final_price = convert_price(final_price_tag.text) if final_price_tag else 0
 
        # Original/base price
        base_price_tag = product_card.find('span', class_='q6wH9+Ht7LxnxrEgD22BCQ==')
        base_price = convert_price(base_price_tag.text) if base_price_tag else final_price
 
        # Discount percent
        discount_tag = product_card.find('span', class_='vRrrC5GSv6FRRkbCqM7QcQ==')
        discount_percent = float(discount_tag.text.replace("%", "").strip()) if discount_tag else 0
 
        return [product_name, base_price, final_price, discount_percent]
    except Exception as e:
        print(f"Failed to parse product card: {e}")
        return None
 
def get_product_data(promo_sku, urls):
    
 
    try:
        # Step 1: Crawl general product pages
        for main_url in urls:
            products_data = []
            etalase_links = set()
            for i in range(200):  # Adjust page range as needed
                url = f'https://www.tokopedia.com/{main_url}/product/page/{i}?perpage=10'
                print(f'Collecting data from {url}')
                try:
                    response = http.post(url, headers=headers, verify=False)
                    response.raise_for_status()
                except requests.RequestException as e:
                    print(f"[ERROR] Failed to fetch {url}: {e}")
                    continue  # go to next page or URL
                soup = BeautifulSoup(response.content, 'html.parser')
            
                # Check if there are no products on the page
                empty_msg = soup.find('h5', class_='css-1e3cf11-unf-heading e1qvo2ff5')
                if empty_msg and "Toko ini belum memiliki produk" in empty_msg.text:
                    print(f"Page {i}: No more products.")
                    break
    
                product_cards = soup.find_all('div', class_='css-79elbk')
                for product_card in product_cards:
                    product_info = parse_product_card(product_card)
                    if product_info:
                        product_info.append(main_url)
                        products_data.append(product_info)
    
                # Collect etalase links from sidebar menu (only once)
                if not etalase_links:
                    sidebar_menu = soup.find('ul', class_='css-17mrx6g')
                    if sidebar_menu:
                        for a in sidebar_menu.find_all('a', href=True):
                            href = a['href']
                            if href.startswith(f'/{main_url}/etalase/'):
                                etalase_links.add("https://www.tokopedia.com" + href)
    
                time.sleep(15)
    
            # Step 2: Crawl all products under each etalase
            for etalase_url in etalase_links:
                print(f"Scraping etalase: {etalase_url}")
                for i in range(100):  # Adjust page range per etalase
                    page_url = f"{etalase_url}/page/{i}?perpage=10"
                    try:
                        response = http.post(page_url, headers=headers, verify=False)
                        response.raise_for_status()
                    except requests.RequestException as e:
                        print(f"[ERROR] Failed to fetch {page_url}: {e}")
                        continue
                    soup = BeautifulSoup(response.content, 'html.parser')
                    product_cards = soup.find_all('div', class_='css-79elbk')
                
                    # Check if there are no products on the page
                    empty_msg = soup.find('h5', class_='css-1e3cf11-unf-heading e1qvo2ff5')
                    if empty_msg and "Toko ini belum memiliki produk" in empty_msg.text:
                        print(f"{etalase_url} Page {i}: No more products.")
                        break
                
                    for product_card in product_cards:
                        product_info = parse_product_card(product_card)
                        if product_info:
                            product_info.append(main_url)
                            products_data.append(product_info)
    
                    time.sleep(15)
 
            # Combine with existing DataFrame
            new_df = pd.DataFrame(products_data, columns=["productName", "basePrice", "finalPrice", "discountPercent", "url"])
            promo_sku = pd.concat([promo_sku, new_df], ignore_index=True)
            
        

    except Exception as e:
        print(f"Error: {e}")
 
    return promo_sku
 

from datetime import datetime
current_date = datetime.today()

print("Start Scraping Tokopedia")
print(current_date)
urls = ['rumah-bersih-unilever', 'unilevermall', 'unilever-food', 'unilever', 'unilever-hair-beauty-studio', 
'daily-care-by-unilever', 'unilever-international-shop']

# Execute the function and get the product data
promo_sku = get_product_data(promo_sku, urls)

promo_sku.sort_values('finalPrice', ascending=True, inplace=True)
promo_sku.drop_duplicates(subset=["productName"], keep='first', inplace=True)

parent_folder = "c:/Users/CDF-Automation.Indon/OneDrive - Unilever/Documents/Data Scraping/"
file_name = f"{parent_folder}tokopedia/TOKOPEDIA_{datetime.now().strftime('%y%m%d')}.xlsx"
promo_sku.to_excel(file_name,index=False)
current_date = datetime.today()
print("Finished Scraping Tokopedia")
print(current_date)
print(file_name)