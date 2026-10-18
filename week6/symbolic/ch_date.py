"""CrossHair contracts: api.date() should never return a datetime."""
import datetime as _dt
import re
import tomlkit
from tomlkit._utils import parse_rfc3339

def date_never_returns_datetime(raw: str) -> bool:
    """
    pre: re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}", raw)
    post: _
    """
    try:
        d = tomlkit.date(raw)
    except ValueError:
        return True
    return not isinstance(d, _dt.datetime)
