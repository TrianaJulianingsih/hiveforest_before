from datetime import datetime
from dateutil import parser
from pytz import timezone as pytz_timezone
import logging

logger = logging.getLogger(__name__)

# ╔══════════════════════════════════════════════════════════════╗
# ║  Name: hive_dateparser                                       ║
# ║  Type: Class                                                 ║
# ║  Purpose: Robust date parser for inconsistent source formats ║
# ╟──────────────────────────────────────────────────────────────╢
# ║  Path: apps\base\utils\chronos.py                            ║
# ║  Created: Jun/27-2025 by Setiadji                            ║
# ║  Updates: Aug/1-2025 by Setiadji                             ║
# ╚══════════════════════════════════════════════════════════════╝
def hive_dateparser(date_str, *, allow_fallback=True, raise_error=False, tz=None):
    """
    A robust date parser with optional timezone awareness.

    - tz: a pytz timezone object (e.g., pytz.timezone("Asia/Jakarta"))
    """
    if not date_str:
        return None

    cleaned = str(date_str).strip().replace("'", "").title()

    known_formats = [
        "%d-%b-%y %I.%M.%S.%f %p %z",
        "%d/%m/%Y %H:%M:%S",
        "%d-%b-%y %H:%M:%S",
        "%d-%b-%Y %H:%M:%S",
        "%d-%b-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]

    for fmt in known_formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            if parsed.tzinfo is None and tz:
                parsed = tz.localize(parsed)
            return parsed
        except:
            continue

    if allow_fallback:
        try:
            parsed = parser.parse(cleaned, dayfirst=True)
            if parsed.tzinfo is None and tz:
                parsed = tz.localize(parsed)
            return parsed
        except Exception as e:
            logger.warning(f"[Hive DateParser] Failed fallback: {cleaned} → {e}")

    if raise_error:
        raise ValueError(f"Hive DateParser failed to parse: {cleaned}")
    return None
