"""Generate synthetic marketing campaign dataset."""

import csv
import random
from pathlib import Path

random.seed(42)

CHANNELS = ["google_ads", "meta_ads", "tiktok_ads", "yandex_direct", "email", "seo"]
MONTHS = [f"2025-{m:02d}-01" for m in range(1, 13)]

# Base metrics per channel (monthly averages)
BASE = {
    "google_ads":     {"impressions": 450000, "clicks": 18000, "conversions": 720, "spend": 850000, "revenue": 2800000},
    "meta_ads":       {"impressions": 600000, "clicks": 15000, "conversions": 540, "spend": 620000, "revenue": 1900000},
    "tiktok_ads":     {"impressions": 800000, "clicks": 24000, "conversions": 360, "spend": 400000, "revenue": 1100000},
    "yandex_direct":  {"impressions": 300000, "clicks": 12000, "conversions": 480, "spend": 520000, "revenue": 1700000},
    "email":          {"impressions": 50000,  "clicks": 8000,  "conversions": 640, "spend": 45000,  "revenue": 1400000},
    "seo":            {"impressions": 200000, "clicks": 22000, "conversions": 880, "spend": 120000, "revenue": 2200000},
}

rows = []
for month_idx, month in enumerate(MONTHS):
    for channel in CHANNELS:
        base = BASE[channel]
        # Seasonal growth trend (+2% per month)
        trend = 1.0 + month_idx * 0.02
        # Random noise ±15%
        noise = lambda: random.uniform(0.85, 1.15)

        row = {
            "date": month,
            "channel": channel,
            "impressions": int(base["impressions"] * trend * noise()),
            "clicks": int(base["clicks"] * trend * noise()),
            "conversions": int(base["conversions"] * trend * noise()),
            "spend": round(base["spend"] * trend * noise(), 2),
            "revenue": round(base["revenue"] * trend * noise(), 2),
        }

        # ANOMALY 1: TikTok spend spike in July (3x spend, same revenue)
        if channel == "tiktok_ads" and month == "2025-07-01":
            row["spend"] = round(row["spend"] * 3.0, 2)

        # ANOMALY 2: Email revenue crash in October (revenue drops 80%)
        if channel == "email" and month == "2025-10-01":
            row["revenue"] = round(row["revenue"] * 0.2, 2)

        rows.append(row)

output = Path(__file__).parent / "demo_campaigns.csv"
with open(output, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "channel", "impressions", "clicks", "conversions", "spend", "revenue"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} rows → {output}")
