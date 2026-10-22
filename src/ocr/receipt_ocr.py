"""
Receipt OCR service for Smart Grocery Rescue.

EasyOCR is imported only when receipt scanning is requested. The reader is
cached so it is not initialized again on every Streamlit rerun.
"""

from functools import lru_cache


@lru_cache(maxsize=1)
def _get_reader():
    """Create and reuse a single English EasyOCR reader."""
    import easyocr

    return easyocr.Reader(["en"], gpu=False)


def extract_text(image_path, min_confidence=0.40):
    """
    Extract receipt text using EasyOCR.

    image_path may be a file path or an image input accepted by EasyOCR,
    including a NumPy array.
    """
    if not 0 <= min_confidence <= 1:
        raise ValueError("min_confidence must be between 0 and 1")

    reader = _get_reader()
    results = reader.readtext(image_path)

    extracted_text = []
    for _, text, confidence in results:
        confidence = float(confidence)
        if confidence >= min_confidence:
            cleaned_text = str(text).strip()
            if cleaned_text:
                extracted_text.append({
                    "text": cleaned_text,
                    "confidence": round(confidence, 4),
                })

    return extracted_text


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.ocr.receipt_ocr <receipt-image-path>")
        raise SystemExit(2)

    for item in extract_text(sys.argv[1]):
        print(f"{item['text']} (confidence: {item['confidence']})")