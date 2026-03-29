import os
import re
import mimetypes
import boto3

from io import BytesIO
from uuid import uuid4
from datetime import datetime
from decimal import Decimal
from PIL import Image
from django.conf import settings


def upload_receipt_to_s3(file_bytes, original_name, content_type, user_id):
    s3 = boto3.client("s3", region_name=settings.AWS_REGION)

    ext = os.path.splitext(original_name)[1]
    key = f"receipts/user_{user_id}/{uuid4().hex}{ext}"

    final_content_type = (
        content_type
        or mimetypes.guess_type(original_name)[0]
        or "application/octet-stream"
    )

    s3.upload_fileobj(
        BytesIO(file_bytes),
        settings.AWS_STORAGE_BUCKET_NAME,
        key,
        ExtraArgs={"ContentType": final_content_type},
    )

    s3_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{key}"
    return key, s3_url


def guess_category_name(merchant):
    merchant = (merchant or "").lower()

    category_map = {
        "tesco": "Food",
        "dunnes": "Food",
        "lidl": "Food",
        "aldi": "Food",
        "supervalu": "Food",
        "amazon": "Shopping",
        "ebay": "Shopping",
        "nike": "Shopping",
        "zara": "Shopping",
        "uber": "Travel",
        "bolt": "Travel",
        "ryanair": "Travel",
        "aerlingus": "Travel",
        "boots": "Health",
        "pharmacy": "Health",
        "hospital": "Health",
        "electric": "Bills",
        "gas": "Bills",
        "internet": "Bills",
    }

    for key, value in category_map.items():
        if key in merchant:
            return value

    return "Other"


def preprocess_image_for_ocr(file_bytes):
    import numpy as np
    import cv2

    image = Image.open(BytesIO(file_bytes)).convert("RGB")
    img_np = np.array(image)
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    return img_bgr


def extract_text_with_rapidocr(file_bytes):
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return ""

    img = preprocess_image_for_ocr(file_bytes)
    ocr_engine = RapidOCR()
    result, _ = ocr_engine(img)

    if not result:
        return ""

    lines = []
    for item in result:
        if len(item) >= 2:
            text = str(item[1]).strip()
            if text:
                lines.append(text)

    return "\n".join(lines)


def extract_merchant(lines, original_name):
    for line in lines[:5]:
        cleaned = line.strip()
        if cleaned and len(cleaned) > 2:
            return cleaned[:255]

    base_name = os.path.basename(original_name)
    return os.path.splitext(base_name)[0][:255]


def extract_amount(lines):
    amount_patterns = [
        r'(?:grand total|total amount|total|amount due|amount|balance due)\s*[:\-]?\s*[€$]?\s*([0-9]+(?:\.[0-9]{2})?)',
        r'[€$]\s*([0-9]+(?:\.[0-9]{2})?)',
        r'\b([0-9]+\.[0-9]{2})\b',
    ]

    found_amounts = []

    for line in lines:
        for pattern in amount_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                try:
                    found_amounts.append(Decimal(match))
                except Exception:
                    pass

    return max(found_amounts) if found_amounts else Decimal("0.00")


def extract_date_value(lines):
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{2}/\d{2}/\d{4})',
        r'(\d{2}-\d{2}-\d{4})',
        r'(\d{2}/\d{2}/\d{2})',
    ]

    for line in lines:
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                value = match.group(1)
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
                    try:
                        return datetime.strptime(value, fmt).date()
                    except ValueError:
                        continue

    return datetime.today().date()


def extract_receipt_data(file_bytes, original_name):
    merchant = "Unknown Merchant"
    amount = Decimal("0.00")
    extracted_date = datetime.today().date()
    raw_text = ""

    try:
        raw_text = extract_text_with_rapidocr(file_bytes)
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if lines:
            merchant = extract_merchant(lines, original_name)
            amount = extract_amount(lines)
            extracted_date = extract_date_value(lines)

    except Exception as e:
        print("OCR ERROR:", str(e))
        raw_text = original_name

    category_name = guess_category_name(merchant)

    return {
        "merchant": merchant,
        "amount": amount,
        "date": extracted_date,
        "raw_text": raw_text,
        "category_name": category_name,
    }