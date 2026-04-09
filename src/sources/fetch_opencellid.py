import os
from dotenv import load_dotenv
import requests

load_dotenv ()
api_key = os.getenv ("OPENCELLID_API_KEY")

url = f"https://download.unwiredlabs.com/ocid/downloads?token={api_key}&file=cell_towers.csv.gz"
output_path = "data/raw/opencellid_towers.gz"


response = requests.get(url, stream = True)
response.raise_for_status()

with open(output_path, "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

print(f"Saved to {output_path}")