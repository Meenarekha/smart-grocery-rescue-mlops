import os
import sys

# --------------------------------------------------
# Add project root to Python path
# --------------------------------------------------

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)

sys.path.insert(0, PROJECT_ROOT)


# --------------------------------------------------
# Imports
# --------------------------------------------------

import streamlit as st

from src.ocr.receipt_ocr import extract_text
from src.ocr.receipt_parser import parse_receipt_items


# --------------------------------------------------
# Streamlit Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Smart Grocery Rescue",
    page_icon="🥦",
    layout="wide"
)


# --------------------------------------------------
# Application Header
# --------------------------------------------------

st.title("🥦 Smart Grocery Rescue")

st.write(
    "Reduce food waste and manage your groceries smarter."
)


# --------------------------------------------------
# Receipt Upload
# --------------------------------------------------

st.header("🧾 Upload Grocery Receipt")

uploaded_file = st.file_uploader(
    "Upload your receipt image",
    type=["jpg", "jpeg", "png"]
)


# --------------------------------------------------
# Process Receipt
# --------------------------------------------------

if uploaded_file is not None:

    # Display uploaded receipt
    st.image(
        uploaded_file,
        caption="Uploaded Receipt",
        use_container_width=True
    )

    # OCR button
    if st.button("🔍 Extract Grocery Items"):

        with st.spinner("Reading receipt..."):

            # Convert uploaded file to bytes
            image_bytes = uploaded_file.getvalue()

            # Extract text using EasyOCR
            ocr_results = extract_text(image_bytes)

            # Parse OCR text into grocery items
            grocery_items = parse_receipt_items(ocr_results)

        # --------------------------------------------------
        # Display Grocery Items
        # --------------------------------------------------

        st.subheader("🛒 Detected Grocery Items")

        if grocery_items:

            for item in grocery_items:
                st.write(f"✅ {item}")

        else:

            st.warning(
                "No grocery items could be detected from the receipt."
            )