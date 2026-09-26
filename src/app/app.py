"""
SMART GROCERY RESCUE SYSTEM - Production Application Interface
Final-Year MLOps Engineering Project
Author: Meenarekha & Engineering Team
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st
from PIL import Image

# Pipeline Imports
from src.analytics.waste_analytics import WasteAnalytics
from src.expiry.shelf_life import (
    calculate_expiry_date,
    get_shelf_life,
    load_shelf_life_data,
    normalize_food_name,
)
from src.feedback.feedback_manager import FeedbackManager
from src.nutrition.nutrition_service import NutritionService
from src.ocr.receipt_ocr import extract_text_from_image
from src.ocr.receipt_parser import parse_receipt_lines
from src.recommendation.recipe_recommender import RecipeRecommender

# Initialize System Services
BASE_DIR = Path(__file__).resolve().parent.parent.parent
INVENTORY_FILE = BASE_DIR / "data" / "app" / "grocery_inventory.json"
FEEDBACK_FILE = BASE_DIR / "data" / "app" / "recipe_feedback.json"

st.set_page_config(
    page_title="Smart Grocery Rescue System",
    page_icon="🥦",
    layout="wide",
    initial_sidebar_state="expanded",
)

shelf_life_df = load_shelf_life_data()
recommender = RecipeRecommender()
nutrition_service = NutritionService()
feedback_manager = FeedbackManager(str(FEEDBACK_FILE))

CATEGORY_EMOJI_MAP = {
    "banana": "🍌",
    "apple": "🍎",
    "orange": "🍊",
    "tomato": "🍅",
    "potato": "🥔",
    "onion": "🧅",
    "milk": "🥛",
    "egg": "🥚",
    "bread": "🍞",
    "chicken": "🍗",
    "fish": "🐟",
    "rice": "🍚",
    "pepsi": "🥤",
    "soda": "🥤",
    "cheese": "🧀",
    "carrot": "🥕",
    "broccoli": "🥦",
    "cucumber": "🥒",
    "pasta": "🍝",
    "oil": "🛢️",
    "salt": "🧂",
    "sugar": "🍬",
    "honey": "🍯",
    "chocolate": "🍫",
}


def get_emoji_for_food(food_name: str) -> str:
    cleaned = str(food_name).lower().strip()
    for key, icon in CATEGORY_EMOJI_MAP.items():
        if key in cleaned:
            return icon
    return "🥫"


def load_inventory():
    if not INVENTORY_FILE.exists():
        return []
    try:
        with open(INVENTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_inventory(items):
    INVENTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INVENTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)


def compute_sha256(file_bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


# Navigation Sidebar
st.sidebar.title("🥦 Grocery Rescue")
app_mode = st.sidebar.radio(
    "Navigation Console",
    ["Active Kitchen & Recipes", "Receipt Scanner", "Waste Analytics & History"],
)
st.sidebar.markdown("---")
st.sidebar.caption("Final-Year MLOps Engineering Project | DagsHub + MLflow Architecture")

# ==============================================================================
# MODE 1: ACTIVE KITCHEN & RECIPES
# ==============================================================================
if app_mode == "Active Kitchen & Recipes":
    st.header("Kitchen Inventory & Expiry-Aware Recommender")
    inventory = load_inventory()
    active_groceries = [
        item for item in inventory if item.get("status") in ["Available", "Partially Used"]
    ]

    # SECTION: Expiry Alerts
    now_dt = datetime.now()
    expiring_soon = []
    for item in active_groceries:
        try:
            exp = datetime.strptime(item.get("expiry_date", ""), "%d/%m/%Y")
            d_left = (exp.date() - now_dt.date()).days
            if 0 <= d_left <= 3:
                expiring_soon.append((item, d_left))
        except Exception:
            pass

    if expiring_soon:
        st.error(f"⚠️ Urgent Expiry Warning: {len(expiring_soon)} item(s) expire within 72 hours!")
        cols = st.columns(min(len(expiring_soon), 3))
        for idx, (exp_item, days) in enumerate(expiring_soon):
            with cols[idx % 3]:
                st.warning(f"**{get_emoji_for_food(exp_item['food'])} {exp_item['food']}**\n\nExpires in: {days} day(s)")

    # SECTION: Active Groceries Display
    st.subheader("Current Stock")
    if not active_groceries:
        st.info("No active groceries found. Scan a receipt to log kitchen inventory.")
    else:
        for item in active_groceries:
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 3])
            with col1:
                st.markdown(f"### {get_emoji_for_food(item['food'])}")
            with col2:
                st.markdown(f"**{item['food']}**")
                nut = nutrition_service.get_nutrition_estimate(item.get("standard_food", item["food"]))
                if nut["available"]:
                    st.caption(f"Approx: ~{nut['approx_calories_100g']} kcal / 100g")
                else:
                    st.caption("Approx: Calorie data not available")
            with col3:
                st.caption(f"Purchased: {item.get('purchase_date', 'N/A')}")
                st.caption(f"Expires: {item.get('expiry_date', 'N/A')}")
            with col4:
                st.markdown(f"Status: `{item.get('status')}`")
            with col5:
                new_status = st.selectbox(
                    "Update",
                    ["Available", "Partially Used", "Fully Used", "Discarded"],
                    index=["Available", "Partially Used", "Fully Used", "Discarded"].index(item.get("status")),
                    key=f"status_sel_{item['id']}",
                )
                if new_status != item.get("status"):
                    for inv_it in inventory:
                        if inv_it["id"] == item["id"]:
                            inv_it["status"] = new_status
                            break
                    save_inventory(inventory)
                    st.rerun()
            st.divider()

    # SECTION: Recipe Recommender
    st.markdown("## Expiry-Weighted Recipe Suggestions")
    if not active_groceries:
        st.info("No available groceries for recipe recommendations.")
    else:
        recommendations = recommender.recommend(active_groceries, top_k=5)
        if not recommendations:
            st.warning("No recipes found matching current stock.")
        else:
            for rec in recommendations:
                with st.expander(
                    f"Recipe #{rec['id']} - Cuisine: {rec['cuisine'].capitalize()} (Match: {rec['match_percentage']}%)",
                    expanded=True,
                ):
                    st.progress(min(rec["match_percentage"] / 100.0, 1.0))
                    c_rec1, c_rec2 = st.columns(2)
                    with c_rec1:
                        st.markdown("**Available Ingredients:**")
                        for m in rec["matched_ingredients"]:
                            st.write(f"- {get_emoji_for_food(m)} {m}")
                    with c_rec2:
                        st.markdown("**Missing Ingredients:**")
                        for mis in rec["missing_ingredients"]:
                            st.write(f"- ⚪ {mis}")

                    # Nutrition Summary
                    total_cals, counted = nutrition_service.compute_recipe_calories(rec["matched_ingredients"])
                    if total_cals:
                        st.info(f"Total approximate matched calories: ~{total_cals} kcal across {counted} verified items.")

                    # User Feedback Controls
                    fb_col1, fb_col2, fb_col3 = st.columns(3)
                    with fb_col1:
                        if st.button("👍 Useful Recipe", key=f"fb_like_{rec['id']}"):
                            feedback_manager.record_feedback(rec["id"], rec["cuisine"], "like")
                            st.success("Feedback saved! Recommendations updated.")
                            st.rerun()
                    with fb_col2:
                        if st.button("👎 Not Useful", key=f"fb_dislike_{rec['id']}"):
                            feedback_manager.record_feedback(rec["id"], rec["cuisine"], "dislike")
                            st.warning("Preference saved.")
                            st.rerun()
                    with fb_col3:
                        if st.button("🍳 Cooked This", key=f"fb_cook_{rec['id']}"):
                            feedback_manager.record_feedback(rec["id"], rec["cuisine"], "cooked")
                            st.balloons()
                            st.rerun()

# ==============================================================================
# MODE 2: RECEIPT SCANNER
# ==============================================================================
elif app_mode == "Receipt Scanner":
    st.header("Receipt Ingestion Engine")
    st.markdown("Upload receipt to extract grocery items and calculate shelf-life.")

    uploaded_file = st.file_uploader("Upload Receipt Image", type=["png", "jpg", "jpeg"])

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        receipt_hash = compute_sha256(file_bytes)
        img = Image.open(uploaded_file)
        st.image(img, caption="Receipt Preview", width=350)

        if st.button("Analyze Receipt"):
            with st.spinner("Processing OCR text..."):
                ocr_lines, raw_date = extract_text_from_image(img)
                parsed_groceries = parse_receipt_lines(ocr_lines)

            st.write(f"**Detected Date:** {raw_date if raw_date else 'Using System Date'}")
            purchase_date = raw_date if raw_date else datetime.now().strftime("%d/%m/%Y")

            # Check Duplicates via Image Hash
            current_inv = load_inventory()
            existing_hashes = {it.get("receipt_hash") for it in current_inv if "receipt_hash" in it}

            if receipt_hash in existing_hashes:
                st.warning("Duplicate receipt: This image has already been ingested.")
            else:
                new_items = []
                r_short_id = receipt_hash[:8]

                for idx, g_item in enumerate(parsed_groceries):
                    clean_name = g_item if isinstance(g_item, str) else g_item.get("name", str(g_item))
                    std_food = normalize_food_name(clean_name, shelf_life_df)
                    days, storage = get_shelf_life(std_food, shelf_life_df)
                    exp_date = calculate_expiry_date(purchase_date, days)

                    new_items.append({
                        "id": f"GR-{r_short_id}-{idx+1}",
                        "receipt_id": r_short_id,
                        "receipt_hash": receipt_hash,
                        "food": clean_name,
                        "standard_food": std_food,
                        "purchase_date": purchase_date,
                        "shelf_life_days": days,
                        "storage": storage,
                        "expiry_date": exp_date,
                        "status": "Available",
                        "created_at": datetime.now().isoformat(),
                    })

                current_inv.extend(new_items)
                save_inventory(current_inv)
                st.success(f"Added {len(new_items)} item(s) to inventory.")
                st.rerun()

# ==============================================================================
# MODE 3: WASTE ANALYTICS & HISTORY
# ==============================================================================
elif app_mode == "Waste Analytics & History":
    st.header("Kitchen Waste & Sustainability Dashboard")
    inv = load_inventory()
    metrics = WasteAnalytics.calculate_ledger_metrics(inv)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Items", metrics["total_items"])
    c2.metric("Rescue Rate", f"{metrics['rescue_rate_pct']}%")
    c3.metric("Waste Rate", f"{metrics['waste_rate_pct']}%")
    c4.metric("Active Expired", metrics["expired_active"])

    st.markdown("---")
    c_graph1, c_graph2 = st.columns(2)

    with c_graph1:
        st.subheader("Inventory Status")
        status_df = WasteAnalytics.get_status_distribution_df(inv)
        if not status_df.empty and status_df["Count"].sum() > 0:
            st.bar_chart(status_df.set_index("Status"))
        else:
            st.caption("No inventory data logged.")

    with c_graph2:
        st.subheader("Purchase Frequency")
        timeline_df = WasteAnalytics.get_timeline_dataframe(inv)
        if not timeline_df.empty:
            st.line_chart(timeline_df.set_index("Purchase Date"))
        else:
            st.caption("No purchase timelines recorded.")

    # Month-Wise Expired Items Archive
    st.markdown("### Expired Grocery History")
    expired_records = []
    now_dt = datetime.now()
    for item in inv:
        try:
            exp_dt = datetime.strptime(item.get("expiry_date", ""), "%d/%m/%Y")
            if exp_dt.date() < now_dt.date():
                expired_records.append(item)
        except Exception:
            pass

    if expired_records:
        exp_df = pd.DataFrame(expired_records)[["food", "purchase_date", "expiry_date", "status"]]
        st.dataframe(exp_df, use_container_width=True)
    else:
        st.info("No expired items found.")