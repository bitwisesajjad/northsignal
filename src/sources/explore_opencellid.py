import pandas as pd

df = pd.read_csv("data/raw/opencellid_towers.gz")
df = df[df["mcc"] == 244]
df.to_csv("data/raw/opencellid_finland.csv", index=False)
print(f"Finnish towers: {len(df)}")