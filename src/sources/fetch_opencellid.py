import os
from dotenv import load_dotenv
import requests
import pandas as pd

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

print (" extracting Finland's towers ... ")

df = pd.read_csv ("data/raw/opencellid_towers.gz")
df = df [df ["mcc"] == 244]
df.to_csv ("data/raw/finland.csv")
print (len(df))