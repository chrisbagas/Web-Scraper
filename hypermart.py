from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup


targets = ['clear shampoo', 'sunsilk shampoo', 'lifebuoy', 'tresemme shampoo', 'ponds',
           'glow lovely', 'vaseline', 'pepsodent',
           'closeup', 'lifebuoy sabun mandi', 'lux botanicals', 'rexona', 'axe', 'molto', 'sunlight',
           'wipol', 'vixal', 'royco', 'bango kecap', 'sariwangi',  'buavita',
           'head shoulders', 'pantene shampoo', 'zinc', 'garnier', 'nivea',
           'marina', 'ciptadent pasta gigi', 'nuvo', 'giv', 'posh men body spray',
           'soklin', 'downy pelembut', 'garnier'
           'mama lemon', 'supersol', 'yuri porstex', 'masako',
           'sedaap kecap', 'abc kecap manis', 'sosro teh', 'sosro teh asli', 'tong tji',
           'country choice', 'citra', 'superpel', 'rinso', 'rejoice', 'posh']

locations = {"Cibubur": 21, "Puri Indah": 6,
             "East Coast Surabaya": 32, "Metropolish": 198, "Gading Serpong": 8}


# Function to convert price string into a float/int
def convert_price(price_str):
    # Remove "Rp" and "." then convert to int
    return int(price_str.replace("Rp", "").replace(".", "").strip())


promo_sku = pd.DataFrame(
    columns=["productName", "basePrice", "finalPrice", "location"])


for location_name, store_id in locations.items():
    session = requests.Session()

    # Set the 'store' cookie to the store ID for the location
    # Convert to string for compatibility
    session.cookies.set('store', str(store_id))
    for i in targets:

        response = session.post(
            f'https://shop.hypermart.co.id/hypermart/product-list.php?q={i}&sz=80')
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all product containers
        products = soup.find_all('div', class_='col')

        # List to hold the product data for this location
        products_data = []

        # Iterate over each product
        for product in products:
            # Extract the product name (inside <h5> tag)
            name = product.find('h5').text.strip()

            # Extract the price details (inside <p> tag)
            price_tag = product.find('p')

            if price_tag:
                # Check if there's a span (indicates original price)
                span_tag = price_tag.find('span')

                if span_tag and span_tag.text.strip():
                    # Original price is inside span
                    original_price = convert_price(span_tag.text.strip())
                    # Convert original_price back to string for the replace operation
                    original_price_str = span_tag.text.strip()  # Use the string from span_tag
                    # Discounted price is outside the span
                    discounted_price = convert_price(
                        price_tag.text.replace(original_price_str, '').strip())
                else:
                    # No span means the price outside is the original price
                    original_price = convert_price(price_tag.text.strip())
                    discounted_price = original_price
                products_data.append(
                    [name, original_price, discounted_price, location_name])

        # Append the data for this location to the main DataFrame
        promo_sku = pd.concat([promo_sku, pd.DataFrame(products_data, columns=[
                              "productName", "basePrice", "finalPrice", "location"])], ignore_index=True)

# Drop duplicates based on product name and location
promo_sku.drop_duplicates(subset=["productName", "location"], inplace=True)


file_name = f"./HYPERMART_{datetime.now().strftime('%y%m%d')}.xlsx"
promo_sku.to_excel(file_name, index=False)
