from __future__ import annotations
import json
from pathlib import Path

_PHONE_RULES_PATH = Path(__file__).parent.parent.parent.parent / "rules" / "phone_rules.json"
PHONE_RULES: dict = json.loads(_PHONE_RULES_PATH.read_text(encoding="utf-8"))

COUNTRY_NAMES = {k: v["name"] for k, v in PHONE_RULES.items()}


def generate_insights(
    health_score: float,
    total_rows: int,
    error_breakdown: dict,
    country_breakdown: dict,
    top_failures: list[dict],
) -> list[dict]:
    insights = []
    total_errors = sum(error_breakdown.values()) or 1

    if health_score < 50:
        insights.append({
            "severity": "CRITICAL",
            "title": "Critical Data Quality Alert",
            "body": f"Dataset health score is {health_score:.1f}/100 — below the critical threshold of 50. "
                    f"Do not process this file downstream without significant remediation.",
            "affected_count": total_rows,
        })
    elif health_score < 80:
        insights.append({
            "severity": "WARNING",
            "title": "Below-Average Data Quality",
            "body": f"Health score of {health_score:.1f}/100 indicates significant issues. "
                    f"Review all ERROR-level failures before downstream use.",
            "affected_count": total_rows,
        })
    else:
        insights.append({
            "severity": "INFO",
            "title": "Acceptable Data Quality",
            "body": f"Dataset health score is {health_score:.1f}/100. "
                    f"Proceed after reviewing any WARNING-level items.",
            "affected_count": 0,
        })

    if country_breakdown:
        top_country, top_count = max(country_breakdown.items(), key=lambda x: x[1])
        pct = round(top_count / total_errors * 100, 1)
        if pct > 25:
            country_name = COUNTRY_NAMES.get(top_country, top_country)
            insights.append({
                "severity": "WARNING",
                "title": f"High Error Concentration in {country_name}",
                "body": f"{pct}% of all validation failures originate from {country_name} ({top_country}) records. "
                        f"Investigate your {country_name} data ingestion pipeline for systematic issues.",
                "affected_count": top_count,
            })

    phone_errors = error_breakdown.get("PHONE", 0)
    if phone_errors > 0:
        pct = round(phone_errors / total_errors * 100, 1)
        insights.append({
            "severity": "WARNING" if pct > 10 else "INFO",
            "title": "Phone Number Formatting Issues",
            "body": f"{phone_errors} phone validation failures ({pct}% of all errors). "
                    f"Most common cause: country prefix (+91, +65) included in local number field, "
                    f"or spaces and dashes not stripped. Use the Auto-Fix to resolve strippable cases.",
            "affected_count": phone_errors,
        })

    date_errors = error_breakdown.get("DATE", 0)
    if date_errors > 0:
        pct = round(date_errors / total_errors * 100, 1)
        insights.append({
            "severity": "WARNING",
            "title": "Date Format Inconsistency Detected",
            "body": f"{date_errors} date/timestamp errors ({pct}% of all errors). "
                    f"Most failures occur when MM/DD/YYYY (US format) is mixed with DD/MM/YYYY (EU/Asia format). "
                    f"Standardize all date fields to ISO 8601 (YYYY-MM-DD) at the data entry layer.",
            "affected_count": date_errors,
        })

    payment_errors = error_breakdown.get("PAYMENT", 0)
    if payment_errors > 0:
        insights.append({
            "severity": "WARNING",
            "title": "Unknown Payment Modes Found",
            "body": f"{payment_errors} payment mode mismatches detected. "
                    f"This may indicate a new payment provider not yet added to validation rules, "
                    f"or typos in the payment_mode field (e.g., 'UPI transfer' instead of 'UPI').",
            "affected_count": payment_errors,
        })

    dup_errors = error_breakdown.get("DUPLICATE", 0)
    if dup_errors > 0:
        insights.append({
            "severity": "CRITICAL" if dup_errors > 50 else "WARNING",
            "title": f"{dup_errors} Duplicate Order IDs",
            "body": f"{dup_errors} duplicate order IDs detected. "
                    f"This strongly suggests ETL merge conflicts, double-submission bugs, "
                    f"or incomplete deduplication in your data pipeline. "
                    f"Resolve before any revenue reporting.",
            "affected_count": dup_errors,
        })

    integrity_errors = error_breakdown.get("INTEGRITY", 0)
    if integrity_errors > 0:
        insights.append({
            "severity": "WARNING",
            "title": "Amount Calculation Mismatches",
            "body": f"{integrity_errors} rows where total_amount ≠ unit_price × quantity (>5% tolerance). "
                    f"Potential causes: undisclosed discounts, tax calculation errors, "
                    f"or currency conversion applied mid-row.",
            "affected_count": integrity_errors,
        })

    missing_errors = error_breakdown.get("MISSING", 0)
    if missing_errors > 0:
        insights.append({
            "severity": "CRITICAL",
            "title": "Missing Mandatory Fields",
            "body": f"{missing_errors} mandatory field violations. "
                    f"These rows cannot be processed downstream and require manual intervention or re-collection.",
            "affected_count": missing_errors,
        })

    return insights
