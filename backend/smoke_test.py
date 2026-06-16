import pandas as pd
from app.engine.validation import validate_row
from app.engine.explanation.nlg_engine import explain_error

df = pd.read_csv('sample_transactions.csv', dtype=str).fillna('').head(20)
context = {'seen_order_ids': set()}
total_errors = 0

for i, row in enumerate(df.to_dict('records')):
    errors = validate_row(row, context)
    if errors:
        total_errors += len(errors)
        for err in errors[:1]:  # show first error per row
            exp, suggestion, action = explain_error(err)
            fix_label = action if action else "FLAG_FOR_REVIEW"
            short_exp = exp[:90] + "..." if len(exp) > 90 else exp
            print(f"Row {i+2}: [{err.error_code}] {short_exp}")
            print(f"  Fix action: {fix_label}")
            print()

print(f"--- {total_errors} errors found in first 20 rows ---")
