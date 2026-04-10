"""Generate realistic РСЯ (Yandex Advertising Network) campaign dataset.

Simulates 6 months of data for an e-commerce store selling electronics.
Includes:
- 8 campaigns (retargeting, look-alike, interests, topics, etc.)
- 3 ad formats (text-image, image-banner, video)
- 2 devices (desktop, mobile)
- Daily granularity
- Realistic РСЯ metrics (CTR 0.3-1.5%, CPC 5-35 RUB)
- Built-in anomalies for detection testing
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(2026)

# --- Campaign definitions ---
CAMPAIGNS = {
    "retargeting_cart": {
        "label": "Ретаргетинг: брошенная корзина",
        "ctr_base": 0.012,  # 1.2% — high for RSY
        "cpc_base": 28,
        "conv_rate": 0.045,  # 4.5%
        "avg_order": 8500,
        "daily_impressions": 15000,
    },
    "retargeting_viewed": {
        "label": "Ретаргетинг: просмотр товаров",
        "ctr_base": 0.008,
        "cpc_base": 18,
        "conv_rate": 0.025,
        "avg_order": 6200,
        "daily_impressions": 25000,
    },
    "lookalike_buyers": {
        "label": "Look-alike: покупатели",
        "ctr_base": 0.006,
        "cpc_base": 15,
        "conv_rate": 0.018,
        "avg_order": 5800,
        "daily_impressions": 40000,
    },
    "interests_electronics": {
        "label": "Интересы: электроника и гаджеты",
        "ctr_base": 0.004,
        "cpc_base": 10,
        "conv_rate": 0.012,
        "avg_order": 4500,
        "daily_impressions": 60000,
    },
    "topics_reviews": {
        "label": "Тематика: сайты обзоров техники",
        "ctr_base": 0.005,
        "cpc_base": 12,
        "conv_rate": 0.015,
        "avg_order": 5200,
        "daily_impressions": 35000,
    },
    "geo_moscow": {
        "label": "Гео: Москва и МО, широкий таргет",
        "ctr_base": 0.003,
        "cpc_base": 22,
        "conv_rate": 0.010,
        "avg_order": 7100,
        "daily_impressions": 80000,
    },
    "promo_seasonal": {
        "label": "Промо: сезонные распродажи",
        "ctr_base": 0.009,
        "cpc_base": 20,
        "conv_rate": 0.032,
        "avg_order": 6800,
        "daily_impressions": 30000,
    },
    "brand_awareness": {
        "label": "Охват: узнаваемость бренда",
        "ctr_base": 0.002,
        "cpc_base": 5,
        "conv_rate": 0.003,
        "avg_order": 3500,
        "daily_impressions": 120000,
    },
}

AD_FORMATS = ["text-image", "image-banner", "video"]
FORMAT_MULTIPLIERS = {
    "text-image":    {"ctr": 1.0, "cpc": 1.0},
    "image-banner":  {"ctr": 1.3, "cpc": 1.15},
    "video":         {"ctr": 1.6, "cpc": 1.4},
}

DEVICES = ["desktop", "mobile"]
DEVICE_MULTIPLIERS = {
    "desktop": {"ctr": 1.0, "cpc": 1.2, "conv": 1.3, "impressions": 0.4},
    "mobile":  {"ctr": 1.1, "cpc": 0.85, "conv": 0.75, "impressions": 0.6},
}

# 6 months: Jan—Jun 2026
START = datetime(2026, 1, 1)
DAYS = 181  # Jan 1 — Jun 30

# Day-of-week seasonality (Mon=0, Sun=6)
DOW_FACTOR = [1.05, 1.08, 1.10, 1.12, 1.15, 0.85, 0.70]

rows = []

for day_offset in range(DAYS):
    date = START + timedelta(days=day_offset)
    date_str = date.strftime("%Y-%m-%d")
    dow = date.weekday()
    dow_mult = DOW_FACTOR[dow]

    # Monthly growth trend (+3% per month)
    month_idx = (date.month - 1)
    trend = 1.0 + month_idx * 0.03

    for camp_id, camp in CAMPAIGNS.items():
        for fmt in AD_FORMATS:
            for device in DEVICES:
                fm = FORMAT_MULTIPLIERS[fmt]
                dm = DEVICE_MULTIPLIERS[device]
                noise = lambda: random.uniform(0.75, 1.30)  # noqa: E731

                impressions = int(
                    camp["daily_impressions"]
                    * dm["impressions"]
                    * dow_mult
                    * trend
                    * noise()
                    / len(AD_FORMATS)  # split across formats
                )

                ctr = camp["ctr_base"] * fm["ctr"] * dm["ctr"] * noise()
                clicks = max(1, int(impressions * ctr))

                cpc = camp["cpc_base"] * fm["cpc"] * dm["cpc"] * noise()
                spend = round(clicks * cpc, 2)

                conv_rate = camp["conv_rate"] * dm["conv"] * noise()
                conversions = max(0, int(clicks * conv_rate))

                revenue = round(conversions * camp["avg_order"] * noise(), 2)

                # --- ANOMALIES ---

                # 1: Бот-трафик на brand_awareness video mobile, 15-20 марта
                #    CTR взлетает до 8%, но конверсий 0
                if (camp_id == "brand_awareness" and fmt == "video"
                        and device == "mobile"
                        and datetime(2026, 3, 15) <= date <= datetime(2026, 3, 20)):
                    impressions = int(impressions * 2.5)
                    clicks = int(impressions * 0.08)  # 8% CTR — bot traffic
                    spend = round(clicks * cpc * 0.3, 2)  # cheap clicks
                    conversions = 0
                    revenue = 0

                # 2: CPC spike на retargeting_cart desktop, 1-7 апреля
                #    Конкуренты залили бюджет — CPC x3
                if (camp_id == "retargeting_cart" and device == "desktop"
                        and datetime(2026, 4, 1) <= date <= datetime(2026, 4, 7)):
                    cpc_spiked = cpc * 3.2
                    spend = round(clicks * cpc_spiked, 2)

                # 3: Промо-кампания в мае — конверсии x2.5
                if (camp_id == "promo_seasonal"
                        and datetime(2026, 5, 1) <= date <= datetime(2026, 5, 14)):
                    conversions = int(conversions * 2.5)
                    revenue = round(revenue * 2.5, 2)

                # 4: Площадка-мусор в interests_electronics image-banner
                #    Февраль — CTR 0.01% но тратит как обычно
                if (camp_id == "interests_electronics" and fmt == "image-banner"
                        and date.month == 2):
                    impressions = int(impressions * 4)
                    clicks = max(1, int(impressions * 0.0001))
                    conversions = 0
                    revenue = 0

                rows.append({
                    "date": date_str,
                    "campaign_id": camp_id,
                    "campaign_name": camp["label"],
                    "ad_format": fmt,
                    "device": device,
                    "impressions": impressions,
                    "clicks": clicks,
                    "ctr": round(clicks / max(impressions, 1) * 100, 4),
                    "cpc": round(spend / max(clicks, 1), 2),
                    "spend": spend,
                    "conversions": conversions,
                    "cpa": round(spend / max(conversions, 1), 2) if conversions > 0 else None,
                    "revenue": revenue,
                    "roas": round(revenue / max(spend, 0.01), 2),
                })

output = Path(__file__).parent / "rsya_campaigns.csv"
with open(output, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "date", "campaign_id", "campaign_name", "ad_format", "device",
        "impressions", "clicks", "ctr", "cpc", "spend",
        "conversions", "cpa", "revenue", "roas",
    ])
    writer.writeheader()
    writer.writerows(rows)

# Summary
total_spend = sum(r["spend"] for r in rows)
total_revenue = sum(r["revenue"] for r in rows)
total_conversions = sum(r["conversions"] for r in rows)
print(f"Generated {len(rows)} rows → {output}")
print(f"Period: {START.strftime('%Y-%m-%d')} — {(START + timedelta(days=DAYS-1)).strftime('%Y-%m-%d')}")
print(f"Campaigns: {len(CAMPAIGNS)}")
print(f"Total spend: {total_spend:,.0f} RUB")
print(f"Total revenue: {total_revenue:,.0f} RUB")
print(f"Total conversions: {total_conversions:,}")
print(f"Overall ROAS: {total_revenue/total_spend:.2f}")
print(f"\nAnomalies embedded:")
print(f"  1. Bot traffic: brand_awareness / video / mobile, Mar 15-20")
print(f"  2. CPC spike: retargeting_cart / desktop, Apr 1-7")
print(f"  3. Promo boost: promo_seasonal, May 1-14")
print(f"  4. Junk placement: interests_electronics / image-banner, Feb")
