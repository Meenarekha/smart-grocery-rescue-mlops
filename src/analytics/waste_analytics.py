"""
Smart Grocery Rescue System - Waste Analytics & Ledger Metrics
Calculates consumption velocity, waste rates, and historical distributions.
All state calculations are derived from local JSON state stores.
"""

from datetime import datetime
from typing import Dict, List, Any
import pandas as pd


class WasteAnalytics:
    """Computes summary statistics and charts from grocery state records."""

    @staticmethod
    def calculate_ledger_metrics(inventory: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extracts categorical breakdowns and waste ratios from local inventory.
        """
        if not inventory:
            return {
                "total_items": 0,
                "available": 0,
                "partially_used": 0,
                "fully_used": 0,
                "discarded": 0,
                "expired_active": 0,
                "waste_rate_pct": 0.0,
                "rescue_rate_pct": 0.0,
            }

        total_items = len(inventory)
        available = sum(1 for item in inventory if item.get("status") == "Available")
        partially_used = sum(1 for item in inventory if item.get("status") == "Partially Used")
        fully_used = sum(1 for item in inventory if item.get("status") == "Fully Used")
        discarded = sum(1 for item in inventory if item.get("status") == "Discarded")

        # Expired items are active items past their expiry date
        now_dt = datetime.now()
        expired_active = 0
        for item in inventory:
            if item.get("status") in ["Available", "Partially Used"]:
                exp_str = item.get("expiry_date", "")
                try:
                    exp_dt = datetime.strptime(exp_str, "%d/%m/%Y")
                    if exp_dt.date() < now_dt.date():
                        expired_active += 1
                except (ValueError, TypeError):
                    continue

        # Terminal items are items no longer open for active household kitchen operations
        resolved_items = fully_used + discarded
        if resolved_items > 0:
            waste_rate_pct = round((discarded / resolved_items) * 100, 1)
            rescue_rate_pct = round((fully_used / resolved_items) * 100, 1)
        else:
            waste_rate_pct = 0.0
            rescue_rate_pct = 0.0

        return {
            "total_items": total_items,
            "available": available,
            "partially_used": partially_used,
            "fully_used": fully_used,
            "discarded": discarded,
            "expired_active": expired_active,
            "waste_rate_pct": waste_rate_pct,
            "rescue_rate_pct": rescue_rate_pct,
        }

    @staticmethod
    def get_status_distribution_df(inventory: List[Dict[str, Any]]) -> pd.DataFrame:
        """Constructs a DataFrame suitable for Streamlit native charts."""
        metrics = WasteAnalytics.calculate_ledger_metrics(inventory)
        data = {
            "Status": ["Available", "Partially Used", "Fully Used", "Discarded"],
            "Count": [
                metrics["available"],
                metrics["partially_used"],
                metrics["fully_used"],
                metrics["discarded"],
            ],
        }
        return pd.DataFrame(data)

    @staticmethod
    def get_timeline_dataframe(inventory: List[Dict[str, Any]]) -> pd.DataFrame:
        """Parses purchase dates to build an aggregate purchase timeline."""
        records = []
        for item in inventory:
            p_date = item.get("purchase_date", "Unknown")
            records.append({"Purchase Date": p_date, "Item": item.get("food", "Item")})

        if not records:
            return pd.DataFrame(columns=["Purchase Date", "Count"])

        df = pd.DataFrame(records)
        summary = df.groupby("Purchase Date").size().reset_index(name="Item Count")
        return summary