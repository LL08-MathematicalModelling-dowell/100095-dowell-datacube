class Config:
    BASE_URL: str = "http://127.0.0.1:8000"
    API_KEY: str | None = None
    TIMEOUT: int = 5
    RETRIES: int = 3
    MONGODB_FIELD_TYPES = [
    "string",       # Textual data
    "number",       # Numeric data
    "object",       # Embedded document
    "array",        # List of values
    "boolean",      # True/False
    "date",         # ISO 8601 date
    "null",         # Null value
    "binary",       # Binary data
    "objectid",     # ObjectId
    "decimal128",   # High-precision decimal
    "regex",        # Regular expression
    "timestamp"     # Timestamp
    ]
