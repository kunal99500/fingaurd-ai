# agent/tools/news_tools.py
"""
Tools for fetching market news and generating investment tips.
Used by: investment node
"""

import os
import httpx
from datetime import datetime
from langchain_core.tools import tool

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


@tool
async def fetch_market_news(query: str = "Indian stock market NSE BSE Nifty") -> list:
    """
    Fetch latest financial news from NewsAPI.
    Returns list of articles with title, source, summary, url.
    Falls back to mock data if no API key is set.
    """
    if not NEWS_API_KEY or NEWS_API_KEY == "your_newsapi_key_here":
        return [
            {
                "title":     "Nifty 50 touches new high amid strong FII inflows",
                "source":    "Economic Times",
                "published": datetime.now().strftime("%Y-%m-%d"),
                "summary":   "Indian markets rallied as FIIs poured in ₹4,200 crore.",
                "url":       "https://economictimes.indiatimes.com",
            },
            {
                "title":     "SIP inflows hit record ₹26,000 crore in latest month",
                "source":    "Mint",
                "published": datetime.now().strftime("%Y-%m-%d"),
                "summary":   "Retail investors stay committed to mutual funds despite volatility.",
                "url":       "https://livemint.com",
            },
            {
                "title":     "RBI holds repo rate steady at 6.5%",
                "source":    "Moneycontrol",
                "published": datetime.now().strftime("%Y-%m-%d"),
                "summary":   "Status quo benefits home loan borrowers and FD holders.",
                "url":       "https://moneycontrol.com",
            },
            {
                "title":     "Gold prices surge — should you invest?",
                "source":    "NDTV Profit",
                "published": datetime.now().strftime("%Y-%m-%d"),
                "summary":   "Sovereign Gold Bonds offer 2.5% interest over gold price appreciation.",
                "url":       "https://ndtvprofit.com",
            },
        ]

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        query,
                    "language": "en",
                    "sortBy":   "publishedAt",
                    "pageSize": 6,
                    "apiKey":   NEWS_API_KEY,
                }
            )
            articles = resp.json().get("articles", [])
            return [
                {
                    "title":     a.get("title", ""),
                    "source":    a.get("source", {}).get("name", ""),
                    "published": (a.get("publishedAt") or "")[:10],
                    "summary":   a.get("description", ""),
                    "url":       a.get("url", ""),
                }
                for a in articles
                if a.get("title") and "[Removed]" not in a.get("title", "")
            ]
        except Exception as e:
            return [{"title": f"News fetch error: {e}", "source": "", "published": "", "summary": "", "url": ""}]


@tool
async def get_investment_tips(monthly_savings: float) -> list:
    """
    Generate personalized investment tips for Indian users based on monthly savings.
    Returns a list of tip strings.
    """
    tips = []

    if monthly_savings <= 0:
        tips += [
            "🚨 You're over budget this month. Focus on reducing expenses before investing.",
            "💡 Try the 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
            "📋 Review your top spending category and set a category limit.",
        ]
    elif monthly_savings < 500:
        tips += [
            f"💰 You saved ₹{monthly_savings:.0f} — great start! Even ₹100/month SIP compounds over time.",
            "📱 Start a SIP on Groww or Zerodha Coin — minimum ₹100/month.",
            "🏦 Open a high-interest savings account (Fi Money, Jupiter) for your emergency fund.",
        ]
    elif monthly_savings < 3000:
        tips += [
            f"✅ ₹{monthly_savings:.0f} saved! Consider a Nifty 50 Index Fund SIP for long-term growth.",
            "📈 Liquid Mutual Funds offer better returns than savings accounts for short-term parking.",
            "🧾 Keep 3 months of expenses as emergency fund before investing in equities.",
            "💳 Avoid EMIs on gadgets/clothes — they quietly drain monthly savings.",
        ]
    else:
        tips += [
            f"🎉 Excellent! ₹{monthly_savings:.0f} saved this month. Time to diversify.",
            "📊 Allocation: 60% Nifty 50 Index Fund, 30% Debt Fund, 10% Sovereign Gold Bond.",
            "🔐 Max out PPF contributions — 7.1% p.a., completely tax-free.",
            "💼 NPS gives extra ₹50,000 deduction under 80CCD(1B) — great for tax saving.",
            "📉 Avoid timing the market — increase SIP amount by 10% every year instead.",
        ]

    # General tips always shown
    tips += [
        "⚡ Rule of 72: at 12% returns your money doubles in 6 years.",
        "🧾 Always maintain 6-month emergency fund before investing in equities.",
        "📚 Beginner? Start: Nifty 50 Index Fund SIP (₹500/month minimum on Groww).",
    ]

    return tips