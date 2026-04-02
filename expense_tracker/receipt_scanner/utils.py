import os
import re
import mimetypes
import boto3

from io import BytesIO
from uuid import uuid4
from datetime import datetime
from decimal import Decimal, InvalidOperation
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
        "tesco": "Groceries",
        "dunnes": "Groceries",
        "lidl": "Groceries",
        "aldi": "Groceries",
        "supervalu": "Groceries",

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
        "electric ireland": "Bills",
        "gas": "Bills",
        "internet": "Bills",
        "vodafone": "Bills",
        "eir": "Bills",
        "three": "Bills",

        "restaurant": "Food",
        "cafe": "Food",
        "mcdonald": "Food",
        "burger king": "Food",
        "kfc": "Food",

        "cinema": "Entertainment",
        "netflix": "Entertainment",
        "spotify": "Entertainment",
    }

    for key, value in category_map.items():
        if key in merchant:
            return value

    return "Other"


def _safe_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


def _clean_money_string(value):
    if not value:
        return ""
    return value.replace(",", "").replace("€", "").replace("$", "").strip()


def preprocess_image_for_ocr(file_bytes):
    import numpy as np
    import cv2

    image = Image.open(BytesIO(file_bytes)).convert("RGB")
    img_np = np.array(image)
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    return img_bgr


def preprocess_pil_image_for_ocr(image):
    import numpy as np
    import cv2

    img_np = np.array(image.convert("RGB"))
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    return img_bgr


def extract_text_with_rapidocr(file_bytes):
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return ""

    try:
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
    except Exception:
        return ""


def extract_text_with_rapidocr_from_pil(image):
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return ""

    try:
        img = preprocess_pil_image_for_ocr(image)
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
    except Exception:
        return ""


def extract_text_from_pdf_bytes(file_bytes):
    text_chunks = []

    # 1. Try direct text extraction
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(BytesIO(file_bytes))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_chunks.append(page_text)
    except Exception:
        pass

    direct_text = "\n".join(text_chunks).strip()
    if direct_text:
        return direct_text

    # 2. Fallback: render first page with PyMuPDF and OCR it
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if len(doc) > 0:
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            image = Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
            ocr_text = extract_text_with_rapidocr_from_pil(image)
            if ocr_text.strip():
                return ocr_text
    except Exception:
        pass

    # 3. Fallback: pdf2image + OCR
    try:
        from pdf2image import convert_from_bytes

        pages = convert_from_bytes(file_bytes, first_page=1, last_page=1)
        if pages:
            ocr_text = extract_text_with_rapidocr_from_pil(pages[0].convert("RGB"))
            if ocr_text.strip():
                return ocr_text
    except Exception:
        pass

    return ""


def extract_raw_text(file_bytes, original_name):
    ext = os.path.splitext(original_name)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf_bytes(file_bytes)

    return extract_text_with_rapidocr(file_bytes)


def extract_merchant(lines, original_name, raw_text=""):
    text_lower = (raw_text or "").lower()

    known_merchants = [
        "electric ireland",
        "tesco",
        "dunnes",
        "lidl",
        "aldi",
        "supervalu",
        "amazon",
        "uber",
        "ryanair",
        "eir",
        "vodafone",
        "three",
    ]

    for merchant in known_merchants:
        if merchant in text_lower:
            return merchant.title()

    ignored_phrases = [
        "your account number",
        "to ask about this bill",
        "billing period",
        "bill summary",
        "date of issue",
        "invoice number",
        "total due",
        "pay by",
        "receipt",
        "tax invoice",
        "full details of your account",
    ]

    for line in lines[:10]:
        cleaned = line.strip()
        if not cleaned or len(cleaned) < 3:
            continue

        lower_line = cleaned.lower()
        if any(phrase in lower_line for phrase in ignored_phrases):
            continue

        if re.search(r"\d{4,}", cleaned):
            continue

        return cleaned[:255]

    base_name = os.path.basename(original_name)
    return os.path.splitext(base_name)[0][:255]


def extract_amount(lines, raw_text=""):
    combined_text = "\n".join(lines)
    if raw_text:
        combined_text = f"{combined_text}\n{raw_text}"

    text = combined_text.lower()

    priority_patterns = [
        r"total\s+due\s*[:\-]?\s*[€$]?\s*([0-9]+(?:[.,][0-9]{2})?)",
        r"total\s+amount\s*[:\-]?\s*[€$]?\s*([0-9]+(?:[.,][0-9]{2})?)",
        r"amount\s+due\s*[:\-]?\s*[€$]?\s*([0-9]+(?:[.,][0-9]{2})?)",
        r"grand\s+total\s*[:\-]?\s*[€$]?\s*([0-9]+(?:[.,][0-9]{2})?)",
        r"balance\s+due\s*[:\-]?\s*[€$]?\s*([0-9]+(?:[.,][0-9]{2})?)",
    ]

    for pattern in priority_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = _safe_decimal(_clean_money_string(match.group(1)))
            if value > 0:
                return value

    generic_patterns = [
        r"[€$]\s*([0-9]+(?:[.,][0-9]{2})?)",
        r"\b([0-9]+\.[0-9]{2})\b",
    ]

    found_amounts = []

    for line in lines:
        for pattern in generic_patterns:
            matches = re.findall(pattern, line, re.IGNORECASE)
            for match in matches:
                value = _safe_decimal(_clean_money_string(match))
                if value > 0:
                    found_amounts.append(value)

    if found_amounts:
        return max(found_amounts)

    return Decimal("0.00")


def extract_date_value(lines, raw_text=""):
    combined_text = "\n".join(lines)
    if raw_text:
        combined_text = f"{combined_text}\n{raw_text}"

    date_patterns = [
        r"date of issue\s*[:\-]?\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})",
        r"date\s*[:\-]?\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})",
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{2}-\d{2}-\d{4})",
        r"(\d{2}/\d{2}/\d{2})",
        r"(\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})",
    ]

    date_formats = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d %b %y",
        "%d %b %Y",
        "%d %B %Y",
        "%d %B %y",
    )

    for pattern in date_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            for fmt in date_formats:
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
        raw_text = extract_raw_text(file_bytes, original_name)
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        if lines:
            merchant = extract_merchant(lines, original_name, raw_text=raw_text)
            amount = extract_amount(lines, raw_text=raw_text)
            extracted_date = extract_date_value(lines, raw_text=raw_text)
        else:
            merchant = os.path.splitext(os.path.basename(original_name))[0][:255]

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