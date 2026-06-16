"""
Full automated correctness audit for XenoGuard AI backend.
Run: python audit_test.py
"""
import sys
import re
import requests
from pathlib import Path

BASE = "http://localhost:8000/v1"
SAMPLE_CSV = Path(__file__).parent / "backend" / "sample_transactions.csv"

PASS = []
FAIL = []

def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name}" + (f" -- {detail}" if detail else ""))

# =========================================================================
# 1. VALIDATION ENGINE UNIT TESTS
# =========================================================================
print("\n=== 1. VALIDATION ENGINE ===")
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.engine.validation import validate_row, VALIDATOR_CHAIN
from app.engine.explanation.nlg_engine import explain_error
from app.engine.fix.fix_engine import fix_engine

check("9 validators in chain", len(VALIDATOR_CHAIN) == 9)

# Base valid row
VALID_ROW = {
    "order_id": "A1", "customer_name": "Test User", "email": "test@example.com",
    "phone": "9876543210", "country_code": "IN", "order_date": "2024-01-15",
    "delivery_date": "2024-01-20", "product_name": "Laptop", "quantity": "1",
    "unit_price": "100.00", "total_amount": "100.00", "payment_mode": "UPI",
    "currency": "INR", "transaction_date": "2024-01-15 10:00:00"
}

# Phone: India expects 10 digits — 5 digits should fail
ctx = {"seen_order_ids": set()}
row = {**VALID_ROW, "phone": "12345"}
errors = validate_row(row, ctx)
phone_err = [e for e in errors if e.error_code == "PHONE_LENGTH_MISMATCH"]
check("Phone too-short detected (IN, 5 digits)", len(phone_err) == 1)

# Phone: India — valid 10 digit phone starting 9
ctx2 = {"seen_order_ids": set()}
row2 = {**VALID_ROW, "phone": "9876543210"}
errors2 = validate_row(row2, ctx2)
phone_errs2 = [e for e in errors2 if "PHONE" in e.error_code]
check("Valid India phone accepted (10 digits, starts 9)", len(phone_errs2) == 0)

# Phone: Singapore 8 digits, must start with 6/8/9
ctx3 = {"seen_order_ids": set()}
row3 = {**VALID_ROW, "country_code": "SG", "phone": "81234567", "currency": "SGD"}
errors3 = validate_row(row3, ctx3)
phone_errs3 = [e for e in errors3 if "PHONE" in e.error_code]
check("Valid Singapore phone accepted (8 digits, starts 8)", len(phone_errs3) == 0)

# Phone: Singapore wrong length
ctx3b = {"seen_order_ids": set()}
row3b = {**VALID_ROW, "country_code": "SG", "phone": "12345", "currency": "SGD"}
errors3b = validate_row(row3b, ctx3b)
sg_err = [e for e in errors3b if "PHONE_LENGTH_MISMATCH" in e.error_code]
check("Singapore phone wrong length detected", len(sg_err) == 1)

# Date validation — invalid date
ctx4 = {"seen_order_ids": set()}
row4 = {**VALID_ROW, "order_date": "32/13/2024"}
errors4 = validate_row(row4, ctx4)
date_err = [e for e in errors4 if "DATE" in e.error_code]
check("Invalid date detected (32/13/2024)", len(date_err) >= 1)

# Date validation — valid date format
ctx4b = {"seen_order_ids": set()}
row4b = {**VALID_ROW, "order_date": "2024-01-15"}
errors4b = validate_row(row4b, ctx4b)
date_err4b = [e for e in errors4b if "DATE" in e.error_code]
check("Valid ISO date accepted (2024-01-15)", len(date_err4b) == 0)

# Email missing @
ctx5 = {"seen_order_ids": set()}
row5 = {**VALID_ROW, "email": "noemail.com"}
errors5 = validate_row(row5, ctx5)
email_err = [e for e in errors5 if "EMAIL" in e.error_code]
check("Invalid email detected (missing @)", len(email_err) == 1)

# Email valid
ctx5b = {"seen_order_ids": set()}
row5b = {**VALID_ROW, "email": "valid@example.com"}
errors5b = validate_row(row5b, ctx5b)
email_ok = [e for e in errors5b if "EMAIL" in e.error_code]
check("Valid email accepted", len(email_ok) == 0)

# Payment mode invalid
ctx6 = {"seen_order_ids": set()}
row6 = {**VALID_ROW, "payment_mode": "Cash on delivery"}
errors6 = validate_row(row6, ctx6)
pay_err = [e for e in errors6 if "PAYMENT" in e.error_code]
check("Invalid payment mode detected", len(pay_err) == 1)

# Payment mode valid
ctx6b = {"seen_order_ids": set()}
row6b = {**VALID_ROW, "payment_mode": "UPI"}
errors6b = validate_row(row6b, ctx6b)
pay_ok = [e for e in errors6b if "PAYMENT" in e.error_code]
check("Valid payment mode accepted (UPI)", len(pay_ok) == 0)

# Cross-field amount mismatch: 5 x 20 = 100, but declared 999
ctx7 = {"seen_order_ids": set()}
row7 = {**VALID_ROW, "quantity": "5", "unit_price": "20.00", "total_amount": "999.00"}
errors7 = validate_row(row7, ctx7)
cross_err = [e for e in errors7 if "AMOUNT" in e.error_code]
check("Cross-field amount mismatch detected (5x20!=999)", len(cross_err) == 1)

# Cross-field correct: 5 x 20.00 = 100.00
ctx7b = {"seen_order_ids": set()}
row7b = {**VALID_ROW, "quantity": "5", "unit_price": "20.00", "total_amount": "100.00"}
errors7b = validate_row(row7b, ctx7b)
cross_ok = [e for e in errors7b if "AMOUNT" in e.error_code]
check("Cross-field correct amounts pass (5x20=100)", len(cross_ok) == 0)

# Duplicate detection
ctx8 = {"seen_order_ids": {"DUP001"}}
row8 = {**VALID_ROW, "order_id": "DUP001"}
errors8 = validate_row(row8, ctx8)
dup_err = [e for e in errors8 if "DUPLICATE" in e.error_code]
check("Duplicate order_id detected", len(dup_err) == 1)

# Unknown country code
ctx9 = {"seen_order_ids": set()}
row9 = {**VALID_ROW, "country_code": "XX"}
errors9 = validate_row(row9, ctx9)
cc_err = [e for e in errors9 if "COUNTRY" in e.error_code]
check("Unknown country code detected", len(cc_err) == 1)

# Missing field
ctx10 = {"seen_order_ids": set()}
row10 = {**VALID_ROW, "customer_name": ""}
errors10 = validate_row(row10, ctx10)
miss_err = [e for e in errors10 if "MISSING" in e.error_code]
check("Missing required field detected (empty customer_name)", len(miss_err) == 1)

# Fully valid row should produce ZERO errors
ctx_clean = {"seen_order_ids": set()}
clean_errors = validate_row(VALID_ROW, ctx_clean)
check("Fully valid row produces 0 errors", len(clean_errors) == 0,
      f"Got {len(clean_errors)} errors: {[e.error_code for e in clean_errors]}")

# =========================================================================
# 2. NLG ENGINE
# =========================================================================
print("\n=== 2. NLG EXPLANATION ENGINE ===")
from app.engine.validation.base import ValidationError as VErr

test_err = VErr(
    field_name="phone", error_code="PHONE_LENGTH_MISMATCH",
    error_category="PHONE", raw_value="12345",
    extra={"country_name": "India", "expected_digits": 10, "actual_digits": 5, "country": "IN"}
)
exp, sug, action = explain_error(test_err)
check("NLG explanation is non-empty", len(exp) > 20, repr(exp[:60]))
check("NLG suggestion is non-empty", bool(sug) and len(sug) > 5, repr(sug))
check("NLG fix action returned", action is not None, repr(action))
check("Phone fix action is STRIP_NON_DIGITS", action == "STRIP_NON_DIGITS", repr(action))

# =========================================================================
# 3. FIX ENGINE
# =========================================================================
print("\n=== 3. FIX ENGINE ===")

# Strip non-digits from phone
row_fix1 = {**VALID_ROW, "phone": "+91-98765-43210"}
fixed1 = fix_engine.apply_fix("STRIP_NON_DIGITS", row_fix1, "phone")
check("STRIP_NON_DIGITS removes +, -, spaces",
      fixed1 is not None and re.match(r"^\d+$", fixed1["phone"]) is not None,
      f"Got: {fixed1}")

# Normalize date
row_fix2 = {**VALID_ROW, "order_date": "15/01/2024"}
fixed2 = fix_engine.apply_fix("NORMALIZE_DATE_ISO", row_fix2, "order_date")
check("NORMALIZE_DATE_ISO converts DD/MM/YYYY to YYYY-MM-DD",
      fixed2 is not None and fixed2["order_date"] == "2024-01-15",
      f"Got: {fixed2}")

# Unparseable date returns None
row_fix3 = {**VALID_ROW, "order_date": "not-a-date-at-all"}
fixed3 = fix_engine.apply_fix("NORMALIZE_DATE_ISO", row_fix3, "order_date")
check("NORMALIZE_DATE_ISO returns None for unparseable date", fixed3 is None)

# Strip currency symbols
row_fix4 = {**VALID_ROW, "total_amount": "$1,234.56"}
fixed4 = fix_engine.apply_fix("STRIP_CURRENCY_SYMBOLS", row_fix4, "total_amount")
check("STRIP_CURRENCY_SYMBOLS removes $ and comma",
      fixed4 is not None and fixed4["total_amount"] == "1234.56",
      f"Got: {fixed4}")

# =========================================================================
# 4. LIVE API CHECKS
# =========================================================================
print("\n=== 4. LIVE API ENDPOINTS ===")
try:
    r = requests.get("http://localhost:8000/health", timeout=4)
    check("GET /health -> 200", r.status_code == 200)
    check("Health returns ok", r.json().get("status") == "ok")
except Exception as e:
    check("GET /health -> 200", False, str(e))

try:
    r = requests.get(f"{BASE}/sessions/nonexistent-session", timeout=4)
    check("GET /sessions/missing -> 404", r.status_code == 404)
except Exception as e:
    check("GET /sessions/missing -> 404", False, str(e))

try:
    r = requests.patch(f"{BASE}/fixes/999999/accept", timeout=4)
    check("PATCH /fixes/missing -> 404", r.status_code == 404)
except Exception as e:
    check("PATCH /fixes/missing -> 404", False, str(e))

# =========================================================================
# 5. UPLOAD + PIPELINE
# =========================================================================
print("\n=== 5. UPLOAD + PIPELINE ===")
session_id = None
check("Sample CSV file exists", SAMPLE_CSV.exists(), str(SAMPLE_CSV))

if SAMPLE_CSV.exists():
    # Use just first 100 rows for a fast test
    import csv, io, time
    rows = []
    with open(SAMPLE_CSV, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows.append(header)
        for i, row in enumerate(reader):
            if i >= 100:
                break
            rows.append(row)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerows(rows)
    csv_bytes = buf.getvalue().encode("utf-8")

    try:
        r = requests.post(
            f"{BASE}/upload",
            files={"file": ("audit_mini.csv", csv_bytes, "text/csv")},
            timeout=15
        )
        check("POST /upload -> 200", r.status_code == 200, r.text[:120])
        if r.status_code == 200:
            data = r.json()
            session_id = data["session_id"]
            check("Upload returns UUID session_id", len(session_id) == 36)
            check("Upload returns PENDING status", data.get("status") == "PENDING")
    except Exception as e:
        check("POST /upload -> 200", False, str(e))

    if session_id:
        time.sleep(2)
        try:
            r = requests.get(f"{BASE}/sessions/{session_id}", timeout=5)
            check("GET /sessions/{id} -> 200", r.status_code == 200)
            sdata = r.json()
            check("Session id matches", sdata.get("session_id") == session_id)
            check("Session status is valid",
                  sdata.get("status") in ("PENDING","PROCESSING","COMPLETED"),
                  f"Got: {sdata.get('status')}")
        except Exception as e:
            check("GET /sessions/{id} -> 200", False, str(e))

        try:
            r = requests.get(f"{BASE}/sessions/{session_id}/preview", timeout=5)
            check("GET /preview -> 200", r.status_code == 200)
            if r.status_code == 200:
                pdata = r.json()
                check("Preview has headers", len(pdata.get("headers", [])) > 0)
                check("Preview has rows", len(pdata.get("rows", [])) > 0)
                check("Preview contains order_id column",
                      "order_id" in pdata.get("headers", []))
                check("Preview contains payment_mode column",
                      "payment_mode" in pdata.get("headers", []))
        except Exception as e:
            check("GET /preview -> 200", False, str(e))

        try:
            r = requests.get(f"{BASE}/events/{session_id}", timeout=3, stream=True)
            check("GET /events SSE -> 200", r.status_code == 200)
            check("SSE Content-Type is text/event-stream",
                  "text/event-stream" in r.headers.get("content-type",""))
            r.close()
        except Exception as e:
            check("GET /events SSE -> 200", False, str(e))

# =========================================================================
# FINAL SUMMARY
# =========================================================================
total = len(PASS) + len(FAIL)
print(f"\n{'='*52}")
print(f"  AUDIT COMPLETE: {len(PASS)}/{total} checks passed")
if FAIL:
    print(f"\n  FAILED ({len(FAIL)}):")
    for f in FAIL:
        print(f"    - {f}")
else:
    print("  ALL CHECKS PASSED! Project is in good condition.")
print("="*52)

sys.exit(0 if not FAIL else 1)
