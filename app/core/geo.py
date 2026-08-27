import random
from pathlib import Path

import geoip2.database
import geoip2.errors

from app.core.config import settings

_SAMPLE_COUNTRY_CODES = ["US", "GB", "DE", "FR", "CA", "AU", "JP", "BR", "IN", "NG"]

_MMDB_PATH = Path(__file__).resolve().parent.parent.parent / "GeoLite2-Country.mmdb"

_reader: geoip2.database.Reader | None = None


def _get_reader() -> geoip2.database.Reader:
    global _reader
    if _reader is None:
        _reader = geoip2.database.Reader(str(_MMDB_PATH))
    return _reader


def resolve_country(ip_address: str) -> str | None:
    if settings.ENVIRONMENT == "development":
        return random.choice(_SAMPLE_COUNTRY_CODES)

    try:
        return _get_reader().country(ip_address).country.iso_code
    except geoip2.errors.AddressNotFoundError:
        return None
