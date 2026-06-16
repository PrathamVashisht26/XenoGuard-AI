import csv
import random
import uuid
from datetime import datetime, timedelta

random.seed(42)

COUNTRIES = [
    {"code": "IN", "name": "India", "valid_digits": 10, "valid_prefix": "9", "currency": "INR"},
    {"code": "SG", "name": "Singapore", "valid_digits": 8, "valid_prefix": "8", "currency": "SGD"},
    {"code": "AE", "name": "UAE", "valid_digits": 9, "valid_prefix": "5", "currency": "AED"},
    {"code": "US", "name": "United States", "valid_digits": 10, "valid_prefix": "4", "currency": "USD"},
]

PAYMENT_MODES = ["CREDIT_CARD", "DEBIT_CARD", "UPI", "NET_BANKING", "CASH", "WALLET", "BANK_TRANSFER"]
INVALID_PAYMENT_MODES = ["Paypal Transfer", "Cash on delivery", "mobile pay", "online"]

PRODUCTS = [
    ("Wireless Headphones", 29.99, 199.99),
    ("Mechanical Keyboard", 49.99, 149.99),
    ("USB-C Hub", 19.99, 79.99),
    ("Gaming Mouse", 24.99, 89.99),
    ("Webcam HD", 39.99, 129.99),
    ("Monitor Stand", 14.99, 59.99),
    ("Smart Watch", 99.99, 399.99),
    ("Laptop Stand", 24.99, 79.99),
]

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]
INVALID_DATE_FORMATS = ["32/13/2024", "not-a-date", "2024-13-01", "99/99/9999"]

CUSTOMER_NAMES = [
    "Priya Sharma", "Rahul Gupta", "Anjali Singh", "Vikram Mehta",
    "Wei Ling", "Ahmad Hassan", "Sarah Johnson", "Li Wei",
    "Rohan Patel", "Meera Nair", "Tan Ah Kow", "Mohammed Al-Rashid",
    "Emily Chen", "David Kumar", "Fatima Al-Zahra", "John Smith",
]


def random_date(start_year=2023, end_year=2024):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def make_phone(country, inject_error=False, error_type=None):
    digits = country["valid_digits"]
    prefix = country["valid_prefix"]
    phone = prefix + "".join([str(random.randint(0, 9)) for _ in range(digits - 1)])
    if inject_error:
        if error_type == "too_long":
            phone = "+91" + phone  # include country prefix
        elif error_type == "too_short":
            phone = phone[:-2]  # remove 2 digits
        elif error_type == "spaces":
            phone = phone[:4] + " " + phone[4:7] + " " + phone[7:]
    return phone


def make_email(name, inject_error=False):
    local = name.lower().replace(" ", ".").replace("-", "")
    domains = ["gmail.com", "yahoo.com", "outlook.com", "example.in", "work.sg"]
    email = f"{local}@{random.choice(domains)}"
    if inject_error:
        errors = [
            lambda e: e.replace("@", ""),       # missing @
            lambda e: e.split("@")[0] + "@",     # missing domain
            lambda e: e + "@@extra",              # double @
        ]
        email = random.choice(errors)(email)
    return email


def make_date(inject_error=False):
    d = random_date()
    if inject_error:
        if random.random() < 0.5:
            return random.choice(INVALID_DATE_FORMATS)
        # Use inconsistent format
        fmt = random.choice(DATE_FORMATS)
        return d.strftime(fmt)
    return d.strftime("%Y-%m-%d")


def generate_row(row_idx, seen_order_ids, inject_error_rate=0.25):
    country = random.choice(COUNTRIES)
    product = random.choice(PRODUCTS)
    name = random.choice(CUSTOMER_NAMES)
    qty = random.randint(1, 10)
    unit_price = round(product[1] + random.uniform(0, product[2] - product[1]), 2)
    total_amount = round(qty * unit_price, 2)

    order_id = str(uuid.uuid4())[:8].upper()
    # 3% chance of duplicate
    if seen_order_ids and random.random() < 0.03:
        order_id = random.choice(list(seen_order_ids))
    else:
        seen_order_ids.add(order_id)

    error_field = None
    if random.random() < inject_error_rate:
        error_field = random.choice([
            "phone_too_long", "phone_too_short", "phone_spaces",
            "date_invalid", "email_invalid", "payment_invalid",
            "qty_negative", "amount_mismatch", "country_unknown"
        ])

    # Phone
    if error_field in ("phone_too_long", "phone_too_short", "phone_spaces"):
        phone = make_phone(country, inject_error=True,
                           error_type=error_field.replace("phone_", ""))
    else:
        phone = make_phone(country)

    # Email
    email = make_email(name, inject_error=(error_field == "email_invalid"))

    # Date
    order_date = make_date(inject_error=(error_field == "date_invalid"))
    delivery_date = make_date()

    # Payment
    if error_field == "payment_invalid":
        payment_mode = random.choice(INVALID_PAYMENT_MODES)
    else:
        payment_mode = random.choice(PAYMENT_MODES)

    # Quantity
    if error_field == "qty_negative":
        qty = -abs(qty)

    # Amount mismatch
    if error_field == "amount_mismatch":
        total_amount = round(total_amount * random.uniform(1.2, 2.0), 2)

    # Country
    if error_field == "country_unknown":
        country_code = random.choice(["XX", "ZZ", "QQ", "INDIA", "SING"])
    else:
        country_code = country["code"]

    return {
        "order_id": order_id,
        "customer_name": name,
        "email": email,
        "phone": phone,
        "country_code": country_code,
        "order_date": order_date,
        "delivery_date": delivery_date,
        "product_name": product[0],
        "quantity": qty,
        "unit_price": unit_price,
        "total_amount": total_amount,
        "payment_mode": payment_mode,
        "currency": country["currency"],
        "transaction_date": random_date().strftime("%Y-%m-%d %H:%M:%S"),
    }


def generate_dataset(num_rows=10000, output_path="sample_transactions.csv"):
    seen_order_ids = set()
    rows = []
    for i in range(num_rows):
        row = generate_row(i, seen_order_ids, inject_error_rate=0.28)
        rows.append(row)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {num_rows} rows -> {output_path}")


if __name__ == "__main__":
    generate_dataset()
