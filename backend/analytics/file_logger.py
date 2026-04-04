import os
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from attrs import asdict


# Setup a dedicated logger for analytics files
ANALYTICS_LOG_DIR = Path(os.getenv('ANALYTICS_LOG_DIR', '/var/log/datacube'))
ANALYTICS_LOG_DIR.mkdir(parents=True, exist_ok=True)

# We'll write different schemas to different files (or same file with schema prefix)
# For simplicity, write all to one file with a type field.
analytics_logger = logging.getLogger('datacube_analytics')
analytics_logger.setLevel(logging.INFO)

# Rotating file handler (10 MB per file, keep 5 backups)
handler = RotatingFileHandler(
    ANALYTICS_LOG_DIR / 'analytics.log',
    maxBytes=10_485_760,
    backupCount=5
)
handler.setFormatter(logging.Formatter('%(message)s'))  # raw JSON only
analytics_logger.addHandler(handler)
analytics_logger.propagate = False

def log_schema(schema_name: str, data_object) -> None:
    """Log any schema object as a JSON line with a '_schema' field."""
    try:
        # Convert dataclass to dict, add schema marker
        log_entry = data_object.__dict__ if hasattr(data_object, '__dict__') else asdict(data_object)
        log_entry['_schema'] = schema_name
        analytics_logger.info(json.dumps(log_entry))
    except Exception as e:
        # Fallback to stderr
        import sys
        print(f"Analytics logging failed: {e}", file=sys.stderr)