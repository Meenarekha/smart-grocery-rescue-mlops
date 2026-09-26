from src.ocr.receipt_parser import parse_receipt_items


def test_parse_receipt_items():
    ocr_results = [
        {"text": "BANANAS", "confidence": 0.95},
        {"text": "M32 WHOLE MILK GAL", "confidence": 0.95},
        {"text": "PC LARGE EGGS", "confidence": 0.95},
        {"text": "M32 WHEAT BREAD", "confidence": 0.95},
        {"text": "PEPSI", "confidence": 0.95},
        {"text": "15/03/2026", "confidence": 0.95},
        {"text": "TOTAL", "confidence": 0.95},
        {"text": "0.99", "confidence": 0.95},
    ]

    result = parse_receipt_items(ocr_results)

    assert isinstance(result, list)
    assert len(result) > 0

    assert "BANANAS" in result
    assert "WHOLE MILK GAL" in result
    assert "PC LARGE EGGS" in result
    assert "WHEAT BREAD" in result
    assert "PEPSI" in result


def test_parse_receipt_items_ignores_invalid_lines():
    ocr_results = [
        {"text": "TOTAL", "confidence": 0.95},
        {"text": "SUBTOTAL", "confidence": 0.95},
        {"text": "15/03/2026", "confidence": 0.95},
        {"text": "0.99", "confidence": 0.95},
        {"text": "AB", "confidence": 0.95},
        {"text": "APPLE", "confidence": 0.30},
    ]

    result = parse_receipt_items(ocr_results)

    assert result == []