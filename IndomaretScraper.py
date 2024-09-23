import requests
import pandas as pd
from bs4 import BeautifulSoup

from datetime import datetime

# Function to convert price string into a float/int
def convert_price(price_str):
    # Remove "Rp" and "." then convert to int
    return int(price_str.replace("Rp", "").replace(".", "").strip())

targets = ['clear shampoo', 'sunsilk shampoo', 'lifebuoy', 'tresemme shampoo', 'ponds',
           'glow lovely', 'vaseline', 'pepsodent pasta gigi',
           'closeup', 'lifebuoy sabun mandi', 'lux botanicals', 'rexona', 'axe', 'molto', 'sunlight',
           'wipol', 'vixal', 'royco', 'bango kecap', 'sariwangi',  'buavita',
           'head shoulders', 'pantene shampoo', 'zinc', 'garnier', 'nivea',
           'marina', 'ciptadent pasta gigi', 'nuvo', 'giv', 'posh men body spray',
           'soklin softergent', 'soklin liquid', 'soklin pewangi', 'downy pelembut',
           'mama lemon', 'supersol', 'yuri porstex', 'masako penyedap rasa ayam',
           'sedaap kecap', 'abc kecap manis', 'sosro teh', 'sosro teh asli', 'tong tji',
           'country choice', 'citra', 'superpel']

promo_sku = pd.DataFrame(columns=["productName", "basePrice", "finalPrice", "discountPercent"])
# targets = ['teh bendera']
for target in targets:
    url = f"https://www.klikindomaret.com/search/?key={target}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.klikindomaret.com/"
    }

    response = requests.get(url, headers=headers)
    # print(response.cookies)

    soup = BeautifulSoup(response.text, "html.parser")
    
    #Check if the search result is empty
    if not soup.select_one('.produk .rightside .box-item.wrp-noFilter'):
        print(f"No result for {target}")
        continue
    products = soup.find_all("div", class_="each-item")
    # List to hold the product data
    products_data = []
    
    # Loop through the products and extract the title and price
    for product in products:
        # Extract the title
        title = product.find("div", class_="title")
        if title is not None:
            title_text = title.text.strip()
            # Extract the price
            final_price = product.find("span", class_="normal price-value")
            if final_price:
                final_price = convert_price(final_price.text.strip())
            
            base_price = product.find("span", class_="strikeout disc-price")
            discount_percentage = product.find("span", class_="discount")
            
            if base_price and discount_percentage:
                base_price = convert_price(base_price.text.strip().split("\n")[-1])
                discount_percentage = float(discount_percentage.text.strip().replace("%", "").strip())
            else:
                base_price = final_price
                discount_percentage = 0
            
            
        products_data.append([title_text, base_price, final_price, discount_percentage])
    # print(products_data)
            
    promo_sku = pd.concat([promo_sku, pd.DataFrame(products_data, columns=["productName", "basePrice", "finalPrice", "discountPercent"])], ignore_index=True)

promo_sku.drop_duplicates(subset=["productName"], inplace=True)
print(promo_sku)


file_name = f"INDOMARET_{datetime.now().strftime('%y%m%d')}.xlsx"
promo_sku.to_excel(file_name,index=False)