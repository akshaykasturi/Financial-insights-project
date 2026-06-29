# get_ticker_list.py — run this once to extract what we need

import pandas as pd

df = pd.read_csv("exports/monthly_summary.csv")
tickers_sectors = df[["Ticker", "Sector"]].drop_duplicates().sort_values("Ticker")

print(f"Total tickers: {len(tickers_sectors)}\n")
print("TICKERS = [")
for t in tickers_sectors["Ticker"]:
    print(f'    "{t}",')
print("]\n")

print("SECTOR_MAP = {")
for _, row in tickers_sectors.iterrows():
    print(f'    "{row["Ticker"]}": "{row["Sector"]}",')
print("}")