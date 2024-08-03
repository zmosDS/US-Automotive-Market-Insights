import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from urllib.parse import parse_qs, urlparse

# Base URL and headers for the request
# Using Chevrolet as example
url_template = "https://www.cars.com/shopping/results/?page={}&page_size=100&sort=listed_at_desc&stock_type=used&makes[]=chevrolet&year_max=2024&year_min=2010&zip=00000"
headers = {'User-Agent': 'Safari/537.3'}

# Naming the columns for the DataFrame
df_columns = ['Listing ID', 'Trim', 'Make', 'Year', 'Model', 'Price', 'Body Style', 'City', 'State', 'Mileage', 'Stock Type']

# Scrape pages function
def scrape_pages(scrape_all_pages=False, max_pages=100): # significantly diminishing returns after 100 pages
    start_time = time.time()  # Start timer
    page_number = 1
    listings_collected = set()
    rows_list = []  # List to collect each row dictionary

    while True:
        url = url_template.format(page_number)
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        vehicle_cards = soup.find_all('div', class_='vehicle-card')

        # Check if there are vehicle cards on the page or if the maximum page limit has been reached
        if not vehicle_cards or (not scrape_all_pages and page_number >= max_pages):
            break

        for card in vehicle_cards:
            button_element = card.find('button', {'data-qa': 'vehicle-badging'})
            if button_element and 'data-contents' in button_element.attrs:
                data_contents = button_element['data-contents']
                data_dict = json.loads(data_contents)
                href_data = data_dict.get('href_to_vdp', {}).get('href_to_vdp', '')

                # Parse the href data to extract vehicle information
                query_params = parse_qs(urlparse(href_data).query)

                listing_id = query_params.get('listing_id', [None])[0]
                trim = query_params.get('trim', [None])[0]
                make = query_params.get('make', [None])[0]
                model_year = query_params.get('model_year', [None])[0]
                model = query_params.get('model', [None])[0]
                price = query_params.get('price', [None])[0]
                bodystyle = query_params.get('bodystyle', [None])[0]
                stock_type = query_params.get('stock_type', [None])[0]

                # Check for duplicates using 'listing_id'
                if listing_id in listings_collected:
                    continue
                listings_collected.add(listing_id)

                city_state_text = card.select_one('div[data-qa="miles-from-user"]')
                city, state = (None, None)
                if city_state_text:
                    location_parts = city_state_text.get_text(strip=True).split(',')
                    if len(location_parts) >= 2:
                        city = location_parts[0].strip()
                        state = location_parts[1].split(' ')[1].strip()

                mileage_text = card.find('div', {'data_qa': 'mileage'})
                mileage = None
                if mileage_text:
                    mileage = mileage_text.get_text(strip=True).replace(' mi.', '').replace(',', '')

                # Extract details and add to the list of rows
                rows_list.append({
                    'Listing ID': listing_id,
                    'Trim': trim,
                    'Make': make,
                    'Year': model_year,
                    'Model': model,
                    'Price': price,
                    'Body Style': bodystyle,
                    'City': city,
                    'State': state,
                    'Mileage': mileage,
                    'Stock Type': stock_type
                })

        page_number += 1 # Changes page in URL
        time.sleep(.5)  # Sleep for 0.5 seconds between requests

    # Create a DataFrame from the list of rows
    df = pd.DataFrame(rows_list, columns=df_columns)
    end_time = time.time()  # End timer
    print(f"Scraping completed in {end_time - start_time:.2f} seconds.")
    return df

df_100_pages = scrape_pages()

# Save the DataFrame to a CSV file
df_100_pages.to_csv('Chevrolet Scrape.csv', index=False)

print('Chevrolet 100 page scrape completed (date).')