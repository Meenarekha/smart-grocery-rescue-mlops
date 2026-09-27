"""
SMART GROCERY RESCUE SYSTEM
Production Streamlit Application
"""

import hashlib
import io
import json
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

# ---------------------------------------------------------------------------
# Pipeline Imports
# ---------------------------------------------------------------------------

from src.analytics.waste_analytics import WasteAnalytics

from src.expiry.shelf_life import (
    calculate_expiry_date,
    get_shelf_life,
    load_shelf_life_data,
    normalize_food_name,
)

from src.feedback.feedback_manager import FeedbackManager
from src.nutrition.nutrition_service import NutritionService
from src.ocr.receipt_ocr import extract_text
from src.ocr.receipt_parser import parse_receipt_items
from src.recommendation.recipe_recommender import RecipeRecommender


# ---------------------------------------------------------------------------
# Project Paths
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent

INVENTORY_FILE = (
    BASE_DIR
    / "data"
    / "app"
    / "grocery_inventory.json"
)

FEEDBACK_FILE = (
    BASE_DIR
    / "data"
    / "app"
    / "recipe_feedback.json"
)


# ---------------------------------------------------------------------------
# Streamlit Configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Smart Grocery Rescue System",
    page_icon="🥦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Initialize Services
# ---------------------------------------------------------------------------

shelf_life_df = load_shelf_life_data()

recommender = RecipeRecommender()

nutrition_service = NutritionService()

feedback_manager = FeedbackManager(
    str(FEEDBACK_FILE)
)


# ---------------------------------------------------------------------------
# Food Category Emojis
# ---------------------------------------------------------------------------

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
    """Return an emoji based on the grocery name."""

    cleaned = str(food_name).lower().strip()

    for key, icon in CATEGORY_EMOJI_MAP.items():
        if key in cleaned:
            return icon

    return "🥫"


def get_expiry_status(expiry_date: str) -> dict:
    """
    Determine the current shelf-life condition of an inventory item.

    Inventory status (Available / Partially Used / Fully Used / Discarded)
    remains independent from expiry condition.
    """
    try:
        expiry = datetime.strptime(str(expiry_date), "%d/%m/%Y").date()
        today = datetime.now().date()
        days_left = (expiry - today).days

        if days_left < 0:
            return {
                "label": "Expired",
                "days_left": days_left,
                "icon": "🔴",
            }

        if days_left == 0:
            return {
                "label": "Expires Today",
                "days_left": 0,
                "icon": "🔴",
            }

        if days_left <= 3:
            return {
                "label": "Expiring Soon",
                "days_left": days_left,
                "icon": "🟠",
            }

        return {
            "label": "Fresh",
            "days_left": days_left,
            "icon": "🟢",
        }

    except (TypeError, ValueError):
        return {
            "label": "Unknown",
            "days_left": None,
            "icon": "⚪",
        }


# ---------------------------------------------------------------------------
# Inventory Functions
# ---------------------------------------------------------------------------

def load_inventory():
    """Load grocery inventory from JSON."""

    if not INVENTORY_FILE.exists():
        return []

    try:
        with open(
            INVENTORY_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


def save_inventory(items):
    """Save grocery inventory to JSON."""

    INVENTORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        INVENTORY_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            items,
            file,
            indent=2,
        )


# ---------------------------------------------------------------------------
# Receipt Hash
# ---------------------------------------------------------------------------

def compute_sha256(file_bytes) -> str:
    """Generate SHA-256 hash for duplicate receipt detection."""

    return hashlib.sha256(file_bytes).hexdigest()


# ---------------------------------------------------------------------------
# Receipt Date Extraction
# ---------------------------------------------------------------------------

def extract_purchase_date(ocr_results):
    """
    Extract a purchase date from OCR results.

    Supported examples:
        15/03/2026
        15-03-2026
        15.03.2026
    """

    date_pattern = re.compile(
        r"\b(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2,4})\b"
    )

    for result in ocr_results:

        text = str(result.get("text", ""))

        match = date_pattern.search(text)

        if not match:
            continue

        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))

        if year < 100:
            year += 2000

        try:
            date_obj = datetime(
                year,
                month,
                day,
            )

            return date_obj.strftime("%d/%m/%Y")

        except ValueError:
            continue

    return None


# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------

st.sidebar.title("🥦 Grocery Rescue")

app_mode = st.sidebar.radio(
    "Navigation Console",
    [
        "Active Kitchen & Recipes",
        "Receipt Scanner",
        "Waste Analytics & History",
    ],
)

st.sidebar.markdown("---")

st.sidebar.markdown(
    """
    <div style="padding: 0.5rem 0 0.2rem 0;">
        <div style="font-size: 0.95rem; font-weight: 600;">
            Your kitchen, smarter.
        </div>
        <div style="font-size: 0.82rem; color: #9ca3af;">
            Less waste. Better use.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div style="
        margin-top: 1.5rem;
        padding-top: 0.8rem;
        border-top: 1px solid rgba(255,255,255,0.10);
        font-size: 0.72rem;
        color: #6b7280;
    ">
        Grocery Rescue · v1.0
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# MODE 1 — ACTIVE KITCHEN & RECIPES
# =============================================================================

if app_mode == "Active Kitchen & Recipes":

    st.header(
        "Kitchen Inventory & Expiry-Aware Recommender"
    )

    inventory = load_inventory()

    active_groceries = [
        item
        for item in inventory
        if item.get("status")
        in [
            "Available",
            "Partially Used",
        ]
    ]

    # -------------------------------------------------------------------------
    # Expiry Alerts
    # -------------------------------------------------------------------------

    now_dt = datetime.now()

    expired_active = []
    expiring_soon = []

    for item in active_groceries:

        try:

            expiry_date = datetime.strptime(
                item.get("expiry_date", ""),
                "%d/%m/%Y",
            )

            days_left = (
                expiry_date.date()
                - now_dt.date()
            ).days

            if days_left < 0:
                expired_active.append(item)

            elif 0 <= days_left <= 3:
                expiring_soon.append(
                    (
                        item,
                        days_left,
                    )
                )

        except Exception:
            continue

    if expired_active:

        st.error(
            f"🔴 {len(expired_active)} active item(s) "
            f"have passed their estimated expiry date."
        )

    if expiring_soon:

        st.warning(
            f"🟠 {len(expiring_soon)} item(s) "
            f"expire within the next 3 days."
        )

        columns = st.columns(
            min(len(expiring_soon), 3)
        )

        for index, (
            expiry_item,
            days_left,
        ) in enumerate(expiring_soon):

            with columns[index % 3]:

                st.warning(
                    f"**"
                    f"{get_emoji_for_food(expiry_item['food'])} "
                    f"{expiry_item['food']}"
                    f"**\n\n"
                    f"Expires in: "
                    f"{days_left} day(s)"
                )

    # -------------------------------------------------------------------------
    # Current Stock
    # -------------------------------------------------------------------------

    st.subheader("Current Stock")

    if not active_groceries:

        st.info(
            "No active groceries found. "
            "Scan a receipt to log kitchen inventory."
        )

    else:

        for item in active_groceries:

            col1, col2, col3, col4, col5 = st.columns(
                [1, 3, 2, 2, 3]
            )

            # Food icon
            with col1:

                st.markdown(
                    f"### "
                    f"{get_emoji_for_food(item['food'])}"
                )

            # Food information
            with col2:

                st.markdown(
                    f"**{item['food']}**"
                )

                nutrition = (
                    nutrition_service.get_nutrition_estimate(
                        item.get(
                            "standard_food",
                            item["food"],
                        )
                    )
                )

                if nutrition["available"]:

                    st.caption(
                        f"Approx: "
                        f"~{nutrition['approx_calories_100g']} "
                        f"kcal / 100g"
                    )

                else:

                    st.caption(
                        "Approx: Calorie data not available"
                    )

            # Dates and expiry condition
            with col3:

                st.caption(
                    f"Purchased: "
                    f"{item.get('purchase_date', 'N/A')}"
                )

                st.caption(
                    f"Expires: "
                    f"{item.get('expiry_date', 'N/A')}"
                )

                expiry_info = get_expiry_status(
                    item.get("expiry_date", "")
                )

                if expiry_info["label"] == "Expired":
                    st.error("🔴 Expired")

                elif expiry_info["label"] == "Expires Today":
                    st.error("🔴 Expires Today")

                elif expiry_info["label"] == "Expiring Soon":
                    st.warning(
                        f"🟠 Expiring Soon · "
                        f"{expiry_info['days_left']} day(s)"
                    )

                elif expiry_info["label"] == "Fresh":
                    st.success("🟢 Fresh")

                else:
                    st.caption("⚪ Expiry unavailable")

            # Inventory status
            with col4:

                st.markdown(
                    f"Status: "
                    f"`{item.get('status', 'Available')}`"
                )

            # Status update
            with col5:

                statuses = [
                    "Available",
                    "Partially Used",
                    "Fully Used",
                    "Discarded",
                ]

                current_status = item.get(
                    "status",
                    "Available",
                )

                if current_status not in statuses:
                    current_status = "Available"

                new_status = st.selectbox(
                    "Update",
                    statuses,
                    index=statuses.index(
                        current_status
                    ),
                    key=f"status_sel_{item['id']}",
                )

                if new_status != item.get("status"):

                    for inventory_item in inventory:

                        if (
                            inventory_item["id"]
                            == item["id"]
                        ):

                            inventory_item[
                                "status"
                            ] = new_status

                            break

                    save_inventory(inventory)

                    st.rerun()

            st.divider()

    # -------------------------------------------------------------------------
    # Recipe Recommendations
    # -------------------------------------------------------------------------

    st.markdown(
        "## Expiry-Weighted Recipe Suggestions"
    )

    if not active_groceries:

        st.info(
            "No available groceries for "
            "recipe recommendations."
        )

    else:

        recommendations = recommender.recommend(
            active_groceries,
            top_k=5,
        )

        if not recommendations:

            st.warning(
                "No recipes found matching current stock."
            )

        else:

            for recommendation in recommendations:

                recipe_id = recommendation["id"]

                cuisine = recommendation[
                    "cuisine"
                ]

                match_percentage = recommendation[
                    "match_percentage"
                ]

                with st.expander(
                    f"Recipe #{recipe_id} - "
                    f"Cuisine: {cuisine.capitalize()} "
                    f"(Match: {match_percentage}%)",
                    expanded=True,
                ):

                    st.progress(
                        min(
                            match_percentage / 100.0,
                            1.0,
                        )
                    )

                    recipe_col1, recipe_col2 = st.columns(2)

                    # Matched ingredients
                    with recipe_col1:

                        st.markdown(
                            "**Available Ingredients:**"
                        )

                        for ingredient in recommendation[
                            "matched_ingredients"
                        ]:

                            st.write(
                                f"- "
                                f"{get_emoji_for_food(ingredient)} "
                                f"{ingredient}"
                            )

                    # Missing ingredients
                    with recipe_col2:

                        st.markdown(
                            "**Missing Ingredients:**"
                        )

                        for ingredient in recommendation[
                            "missing_ingredients"
                        ]:

                            st.write(
                                f"- ⚪ {ingredient}"
                            )

                    # Nutrition
                    total_calories, counted = (
                        nutrition_service.compute_recipe_calories(
                            recommendation[
                                "matched_ingredients"
                            ]
                        )
                    )

                    if total_calories is not None:

                        st.info(
                            f"Total approximate matched "
                            f"calories: ~{total_calories} kcal "
                            f"across {counted} verified items."
                        )

                    # Feedback
                    feedback_col1, feedback_col2, feedback_col3 = (
                        st.columns(3)
                    )

                    with feedback_col1:

                        if st.button(
                            "👍 Useful Recipe",
                            key=f"fb_like_{recipe_id}",
                        ):

                            feedback_manager.record_feedback(
                                recipe_id,
                                cuisine,
                                "like",
                            )

                            st.success(
                                "Feedback saved! "
                                "Recommendations updated."
                            )

                            st.rerun()

                    with feedback_col2:

                        if st.button(
                            "👎 Not Useful",
                            key=f"fb_dislike_{recipe_id}",
                        ):

                            feedback_manager.record_feedback(
                                recipe_id,
                                cuisine,
                                "dislike",
                            )

                            st.warning(
                                "Preference saved."
                            )

                            st.rerun()

                    with feedback_col3:

                        if st.button(
                            "🍳 Cooked This",
                            key=f"fb_cook_{recipe_id}",
                        ):

                            feedback_manager.record_feedback(
                                recipe_id,
                                cuisine,
                                "cooked",
                            )

                            st.success(
                                "Recipe marked as cooked."
                            )

                            st.rerun()


# =============================================================================
# MODE 2 — RECEIPT SCANNER
# =============================================================================

elif app_mode == "Receipt Scanner":

    st.header(
        "Receipt Ingestion Engine"
    )

    st.markdown(
        "Upload receipt to extract grocery items "
        "and calculate shelf-life."
    )

    uploaded_file = st.file_uploader(
        "Upload Receipt Image",
        type=[
            "png",
            "jpg",
            "jpeg",
        ],
    )

    if uploaded_file is not None:

        # Read image bytes once
        file_bytes = uploaded_file.getvalue()

        receipt_hash = compute_sha256(
            file_bytes
        )

        # Open image from bytes
        img = Image.open(
            io.BytesIO(file_bytes)
        ).convert("RGB")

        st.image(
            img,
            caption="Receipt Preview",
            width=350,
        )

        if st.button(
            "Analyze Receipt",
            type="primary",
        ):

            with st.spinner(
                "Processing OCR text..."
            ):

                # EasyOCR works with numpy arrays
                image_array = np.array(img)

                ocr_results = extract_text(
                    image_array
                )

                # Parse OCR results
                parsed_groceries = parse_receipt_items(
                    ocr_results
                )

                # Extract purchase date separately
                raw_date = extract_purchase_date(
                    ocr_results
                )

            # -----------------------------------------------------------------
            # OCR Result Display
            # -----------------------------------------------------------------

            st.subheader(
                "OCR Results"
            )

            if ocr_results:

                with st.expander(
                    "View detected OCR text"
                ):

                    for result in ocr_results:

                        st.write(
                            f"{result['text']} "
                            f""
                            f"(confidence: "
                            f"{result['confidence']})"
                        )

            else:

                st.warning(
                    "No readable text was detected."
                )

            # -----------------------------------------------------------------
            # Purchase Date
            # -----------------------------------------------------------------

            purchase_date = (
                raw_date
                if raw_date
                else datetime.now().strftime(
                    "%d/%m/%Y"
                )
            )

            st.write(
                f"**Detected Date:** "
                f"{raw_date if raw_date else 'Not detected'}"
            )

            if not raw_date:

                st.caption(
                    f"Using system date: "
                    f"{purchase_date}"
                )

            # -----------------------------------------------------------------
            # Parsed Grocery Items
            # -----------------------------------------------------------------

            st.subheader(
                "Detected Grocery Items"
            )

            if parsed_groceries:

                for grocery in parsed_groceries:

                    st.write(
                        f"- "
                        f"{get_emoji_for_food(grocery)} "
                        f"{grocery}"
                    )

            else:

                st.warning(
                    "No grocery items were identified "
                    "from the receipt."
                )

            # -----------------------------------------------------------------
            # Duplicate Receipt Check
            # -----------------------------------------------------------------

            current_inventory = load_inventory()

            existing_hashes = {
                item.get("receipt_hash")
                for item in current_inventory
                if item.get("receipt_hash")
            }

            if receipt_hash in existing_hashes:

                st.warning(
                    "Duplicate receipt: "
                    "This image has already been ingested."
                )

            elif not parsed_groceries:

                st.warning(
                    "No grocery items were found. "
                    "Nothing was added to inventory."
                )

            else:

                # -------------------------------------------------------------
                # Create Inventory Items
                # -------------------------------------------------------------

                new_items = []

                receipt_short_id = receipt_hash[:8]

                purchase_date_obj = datetime.strptime(
                    purchase_date,
                    "%d/%m/%Y",
                )

                for index, grocery_item in enumerate(
                    parsed_groceries
                ):

                    clean_name = (
                        str(grocery_item)
                        .strip()
                    )

                    # Find shelf-life information
                    shelf_info = get_shelf_life(
                        clean_name
                    )

                    # If shelf life is unknown,
                    # don't create an invalid inventory item.
                    if shelf_info is None:

                        st.info(
                            f"Skipped '{clean_name}' "
                            f"because shelf-life information "
                            f"is not available."
                        )

                        continue

                    expiry_date_obj = (
                        calculate_expiry_date(
                            purchase_date_obj,
                            shelf_info[
                                "shelf_life_days"
                            ],
                        )
                    )

                    expiry_date = (
                        expiry_date_obj.strftime(
                            "%d/%m/%Y"
                        )
                    )

                    new_items.append(
                        {
                            "id": (
                                f"GR-"
                                f"{receipt_short_id}-"
                                f"{index + 1}"
                            ),
                            "receipt_id": receipt_short_id,
                            "receipt_hash": receipt_hash,
                            "food": clean_name,
                            "standard_food": shelf_info[
                                "food"
                            ],
                            "purchase_date": purchase_date,
                            "shelf_life_days": shelf_info[
                                "shelf_life_days"
                            ],
                            "storage": shelf_info[
                                "storage"
                            ],
                            "expiry_date": expiry_date,
                            "status": "Available",
                            "created_at": datetime.now().isoformat(),
                        }
                    )

                # -------------------------------------------------------------
                # Save Inventory
                # -------------------------------------------------------------

                if new_items:

                    current_inventory.extend(
                        new_items
                    )

                    save_inventory(
                        current_inventory
                    )

                    st.success(
                        f"Added "
                        f"{len(new_items)} item(s) "
                        f"to inventory."
                    )

                    st.rerun()

                else:

                    st.warning(
                        "No grocery items with known "
                        "shelf-life information were added."
                    )


# =============================================================================
# MODE 3 — WASTE ANALYTICS & HISTORY
# =============================================================================

elif app_mode == "Waste Analytics & History":

    st.header(
        "Waste & Inventory Analytics"
    )

    inventory = load_inventory()

    metrics = (
        WasteAnalytics.calculate_ledger_metrics(
            inventory
        )
    )

    # -------------------------------------------------------------------------
    # Summary Metrics
    # -------------------------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Items",
        metrics["total_items"],
    )

    col2.metric(
        "Rescue Rate",
        f"{metrics['rescue_rate_pct']}%",
    )

    col3.metric(
        "Waste Rate",
        f"{metrics['waste_rate_pct']}%",
    )

    col4.metric(
        "Expired Items",
        metrics["expired_active"],
    )

    st.markdown("---")

    # -------------------------------------------------------------------------
    # Charts
    # -------------------------------------------------------------------------

    chart_col1, chart_col2 = st.columns(2)

    # Status distribution
    with chart_col1:

        st.subheader(
            "Inventory Status"
        )

        status_df = (
            WasteAnalytics.get_status_distribution_df(
                inventory
            )
        )

        if (
            not status_df.empty
            and status_df["Count"].sum() > 0
        ):

            st.bar_chart(
                status_df.set_index(
                    "Status"
                )
            )

        else:

            st.caption(
                "No inventory data logged."
            )

    # Purchase timeline
    with chart_col2:

        st.subheader(
            "Purchase Frequency"
        )

        timeline_df = (
            WasteAnalytics.get_timeline_dataframe(
                inventory
            )
        )

        if not timeline_df.empty:

            st.line_chart(
                timeline_df.set_index(
                    "Purchase Date"
                )
            )

        else:

            st.caption(
                "No purchase timelines recorded."
            )

    # -------------------------------------------------------------------------
    # Expired Grocery History
    # -------------------------------------------------------------------------

    st.markdown(
        "### Expired Grocery History"
    )

    st.caption(
        "Items whose estimated shelf life has passed, "
        "regardless of inventory status."
    )

    expired_records = []

    current_date = datetime.now().date()

    for item in inventory:

        try:

            expiry_date = datetime.strptime(
                item.get(
                    "expiry_date",
                    "",
                ),
                "%d/%m/%Y",
            )

            if expiry_date.date() < current_date:

                expired_records.append(
                    item
                )

        except Exception:
            continue

    if expired_records:

        display_columns = [
            "food",
            "purchase_date",
            "expiry_date",
            "status",
        ]

        exp_df = pd.DataFrame(
            expired_records
        )

        available_columns = [
            column
            for column in display_columns
            if column in exp_df.columns
        ]

        st.dataframe(
            exp_df[available_columns],
            use_container_width=True,
        )

    else:

        st.info(
            "No expired items found."
        )