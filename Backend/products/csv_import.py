"""
All-or-nothing product import from CSV.

Expected header (order does not matter, extra columns are ignored):
    product_code,product_name,category,price,stock_quantity,status

Step 1 validates every row and collects errors with their row numbers
(the header is row 1, so the first product is row 2). Each row goes
through ProductSerializer, the same rules as the "add product" API.
Step 2 runs only if there are no errors at all: every product and its
opening stock movement is saved inside one transaction.
"""

import csv
import io

from django.db import IntegrityError, transaction

from inventory.services import record_opening_stock

from .serializers import ProductSerializer

REQUIRED_COLUMNS = ["product_code", "product_name", "category", "price", "stock_quantity", "status"]
STATUS_VALUES = {"active": True, "inactive": False}
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024
MAX_ROWS = 5000

# serializer field name -> CSV column name, so errors use the names the user sees
FIELD_TO_COLUMN = {"name": "product_name", "is_active": "status"}


class CsvImportError(Exception):
    """Raised when the file can't be imported. Carries a message and optional row errors."""

    def __init__(self, message, row_errors=None):
        super().__init__(message)
        self.message = message
        self.row_errors = row_errors or []


def import_products_from_csv(uploaded_file, user):
    rows = _read_rows(uploaded_file)
    serializers, row_errors = _validate_rows(rows)

    if row_errors:
        raise CsvImportError(
            f"{len(row_errors)} row(s) have errors. Nothing was imported - fix the file and upload it again.",
            row_errors,
        )

    try:
        with transaction.atomic():
            products = []
            for serializer in serializers:
                product = serializer.save()
                record_opening_stock(product, user, reason="Opening stock from CSV import")
                products.append(product)
    except IntegrityError:
        # someone created one of these codes between our check and the insert
        raise CsvImportError("A product code in the file was added by someone else just now. "
                             "Nothing was imported - please try again.")
    return products


def _read_rows(uploaded_file):
    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        raise CsvImportError("The file is too large (maximum 2 MB).")

    try:
        text = uploaded_file.read().decode("utf-8-sig")  # -sig strips the BOM Excel adds
    except UnicodeDecodeError:
        raise CsvImportError("The file must be a UTF-8 encoded CSV file.")

    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        raise CsvImportError("The file is empty.")

    columns = [column.strip().lower() for column in header]
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise CsvImportError("Missing required column(s): " + ", ".join(missing) + ".")

    rows = []
    for row_number, values in enumerate(reader, start=2):
        if not any(value.strip() for value in values):
            continue  # ignore blank lines
        rows.append((row_number, dict(zip(columns, (value.strip() for value in values)))))

    if not rows:
        raise CsvImportError("The file has a header but no product rows.")
    if len(rows) > MAX_ROWS:
        raise CsvImportError(f"The file has too many rows (maximum {MAX_ROWS}).")
    return rows


def _validate_rows(rows):
    serializers = []
    row_errors = []
    first_seen_on = {}  # product code -> row number, to catch duplicates inside the file

    for row_number, row in rows:
        errors = []

        code = row.get("product_code", "").upper()
        if code and code in first_seen_on:
            errors.append(f"product_code: {code} appears more than once in the file "
                          f"(first on row {first_seen_on[code]}).")
        elif code:
            first_seen_on[code] = row_number

        status_text = row.get("status", "").lower()
        if status_text not in STATUS_VALUES:
            errors.append("status: must be Active or Inactive.")

        serializer = ProductSerializer(data={
            "product_code": row.get("product_code", ""),
            "name": row.get("product_name", ""),
            "category": row.get("category", ""),
            "price": row.get("price", ""),
            "stock_quantity": row.get("stock_quantity", ""),
            "is_active": STATUS_VALUES.get(status_text, True),
        })
        if not serializer.is_valid():
            for field, messages in serializer.errors.items():
                column = FIELD_TO_COLUMN.get(field, field)
                errors.extend(f"{column}: {message}" for message in messages)

        if errors:
            row_errors.append({"row": row_number, "errors": errors})
        else:
            serializers.append(serializer)

    return serializers, row_errors
