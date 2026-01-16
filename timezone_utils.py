"""
Timezone utilities for Brasília (UTC-3)
"""
from datetime import datetime, timezone, timedelta

# Brasília timezone (UTC-3)
BRASILIA_TZ = timezone(timedelta(hours=-3))

def now_brasilia():
    """Get current datetime in Brasília timezone"""
    return datetime.now(BRASILIA_TZ)

def now_brasilia_iso():
    """Get current datetime in Brasília timezone as ISO string"""
    return now_brasilia().isoformat()

def now_brasilia_str(fmt="%d/%m/%Y %H:%M:%S"):
    """Get current datetime in Brasília timezone as formatted string"""
    return now_brasilia().strftime(fmt)
