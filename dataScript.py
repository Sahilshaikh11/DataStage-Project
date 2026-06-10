import requests
import csv
import random
from faker import Faker

# Initializing with Indian locale to generate relevant addresses and locations
fake = Faker('en_IN')

NUM_RECORDS = 500
API_URL = "https://api.tvmaze.com/shows"

print("Fetching real-world media data from TVMaze API...")

# Fetch 2 pages of data (approx 250 shows per page) to comfortably exceed 500 records
raw_shows = []
for page in range(3):
    response = requests.get(f"{API_URL}?page={page}", verify=False)
    if response.status_code == 200:
        raw_shows.extend(response.json())
    else:
        print(f"Failed to fetch page {page}")

# Filter for shows that have a valid network/webChannel and a genre
valid_shows = [
    show for show in raw_shows 
    if (show.get('network') or show.get('webChannel')) and show.get('genres')
][:NUM_RECORDS]

print(f"Successfully processed {len(valid_shows)} real media records.")

production_data = []
stock_data = []

# ---------------------------------------------------------
# 1. Generate PRODUCTION Data (Real Show -> Real Network)
# ---------------------------------------------------------
print("Generating production.csv...")
with open('production.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['name', 'vendor'])
    
    for show in valid_shows:
        name = show['name']
        
        # Determine the vendor (Network or Web Streaming Channel)
        if show.get('network'):
            vendor = show['network']['name']
        else:
            vendor = show['webChannel']['name']
            
        production_data.append({'name': name, 'vendor': vendor, 'show_data': show})
        writer.writerow([name, vendor])

# ---------------------------------------------------------
# 2. Generate STOCK Data (Real Genres + Geographic Data)
# ---------------------------------------------------------
print("Generating stock.csv...")
with open('stock.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['stck_nm', 'dpt_No', 'dpt_nm', 'address', 'lctn', 'cntry', 'rt'])
    
    # Assign persistent department IDs based on common genres to maintain consistency
    dept_map = {}
    dept_counter = 10
    
    for i, prod in enumerate(production_data):
        show = prod['show_data']
        primary_genre = show['genres'][0]
        
        if primary_genre not in dept_map:
            dept_map[primary_genre] = dept_counter
            dept_counter += 10
            
        dept_no = dept_map[primary_genre]
        dpt_nm = primary_genre
        
        # Generate SKU
        media_format = random.choice(["BLU", "DVD", "DIG", "4K"])
        stck_nm = f"{media_format}-{primary_genre[:3].upper()}-{fake.random_int(min=1000, max=9999)}"
        stock_data.append(stck_nm)
        
        # Geographic and financial data
        address = fake.street_address()
        lctn = fake.city()
        cntry = "India"
        rt = round(random.uniform(299.0, 2499.0), 2)
        
        # INTENTIONAL DIRTY DATA INJECTION (10% chance)
        # To test your DataStage Transformer string cleansing logic
        if random.random() < 0.10:
            dpt_nm = f"{dpt_nm} {random.choice(['@', '#', '!!'])}"
        if random.random() < 0.10:
            address = f"{address} {random.choice(['$$', '??', '%%'])}"
            
        writer.writerow([stck_nm, dept_no, dpt_nm, address, lctn, cntry, rt])

# ---------------------------------------------------------
# 3. Generate PROFIT Fact Data
# ---------------------------------------------------------
print("Generating profit.csv...")
with open('profit.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['stock_name', 'production_vendor', 'Amount'])
    
    # 1-to-1 mapping for the fact table to ensure Lookup stages succeed
    for i in range(len(valid_shows)):
        stock = stock_data[i]
        prod = production_data[i]
        
        # Revenue is generated to be higher than the base rate to ensure positive profit calculations
        base_amount = random.uniform(3000.0, 25000.0)
        amount = round(base_amount, 2)
        
        writer.writerow([stock, prod['vendor'], amount])

print("Data generation complete! 500 highly-relational records created.")