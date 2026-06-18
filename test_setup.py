import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API key Loaded: {api_key[:8]}...")

exports = ["monthly_summary","sector_summary","top_performers","anomalies"]
for name in exports:
    path  = f"exports/{name}.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"{name}: {len(df)} rows")
    else:
        print(f"Missing: {path}")