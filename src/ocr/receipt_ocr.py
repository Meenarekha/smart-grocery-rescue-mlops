import easyocr


# Initialize EasyOCR
reader = easyocr.Reader(["en"])


def extract_text(image_path, min_confidence=0.40):
    """
    Extract text from a receipt image using EasyOCR.

    Parameters:
        image_path (str): Path to the receipt image.
        min_confidence (float): Minimum OCR confidence required.

    Returns:
        list: Extracted text with confidence scores.
    """

    results = reader.readtext(image_path)

    extracted_text = []

    for _, text, confidence in results:

        # Keep only reasonably confident OCR results
        if confidence >= min_confidence:

            extracted_text.append({
                "text": text.strip(),
                "confidence": round(float(confidence), 4)
            })

    return extracted_text


if __name__ == "__main__":

    image_path = "receipt 2.png"

    results = extract_text(image_path)

    print("\nExtracted Receipt Text:")
    print("-" * 40)

    for item in results:
        print(
            f"{item['text']} "
            f"(confidence: {item['confidence']})"
        )