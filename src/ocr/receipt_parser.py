import re


def parse_receipt_items(ocr_results):
    """
    Convert OCR results into possible grocery item names.
    """

    items = []

    # Words that usually indicate non-product receipt information
    skip_words = [
    "PRICE CHOPPER",
    "SUPERMARKET",
    "STORE",
    "RECEIPT",
    "TRANSACTION",
    "SALE",
    "CASHIER",
    "CARD",
    "REG",
    "SUBTOTAL",
    "SUBTOTA",
    "TOTAL",
    "TOTA",
    "TAX",
    "SAVINGS",
    "PAID WITH",
    "CHANGE",
    "VALUE",
    "TODAY",
    "THANK",
    "VISIT",
    "WEEKLY",
    "PLEASE COME",
    "AGAIN",
    "WWW",
    "GLEN ST",
    "NY",
    "CASH",
    "FOR",
    "YOU SAVED",
    "CANS",
    "MARI"
    ]

    for result in ocr_results:

        text = result["text"].strip()
        confidence = result["confidence"]

        # Ignore low-confidence OCR results
        if confidence < 0.45:
            continue

        # Ignore very short text
        if len(text) < 3 or len(text.strip('"')) < 2:
            continue

        upper_text = text.upper()

        # Ignore known receipt/store information
        if any(word in upper_text for word in skip_words):
            continue

        # Ignore dates
        if re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", text):
            continue

        # Ignore prices
        if re.fullmatch(r"[$€£]?\s*-?\d+[.,]\d{2}", text):
            continue

        # Ignore mostly numeric text
        digit_count = sum(char.isdigit() for char in text)

        if digit_count > len(text) / 2:
            continue

        # Remove price/unit information
        cleaned = re.sub(
            r"@\s*\$?\d+[.,]?\d*\s*/?\s*(LB|KG|OZ)?",
            "",
            text,
            flags=re.IGNORECASE
        )

        # Remove package quantities
        cleaned = re.sub(
            r"\b\d+\s*(CT|PK|PACK|PCS|LB|KG|OZ|GAL)\b",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        # Remove leading product codes such as M32
        cleaned = re.sub(
            r"^[A-Z]\d+\s+",
            "",
            cleaned,
            flags=re.IGNORECASE
        )

        cleaned = cleaned.strip(" -:@")

        if len(cleaned) >= 3:
            items.append(cleaned.upper())

    # Combine consecutive OCR lines that belong to the same product
    combined_items = []

    i = 0

    while i < len(items):

        current = items[i]

        if i + 1 < len(items):

            next_item = items[i + 1]

            # Combine common split product names
            if current in ["PC LARGE", "LARGE"]:
                combined_items.append(current + " " + next_item)
                i += 2
                continue

            if current in ["WHEAT", "WHOLE MILK"]:
                combined_items.append(current + " " + next_item)
                i += 2
                continue

        combined_items.append(current)
        i += 1

    return combined_items


if __name__ == "__main__":

    from receipt_ocr import extract_text

    results = extract_text("receipt 2.png")

    items = parse_receipt_items(results)

    print("\nPossible Grocery Items:")
    print("-" * 40)

    for item in items:
        print(item)