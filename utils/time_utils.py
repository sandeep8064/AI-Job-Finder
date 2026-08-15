
from datetime import datetime, timedelta, timezone

def get_ist_time() -> datetime:
    """Returns the current time in India Standard Time (UTC+5:30)."""
    # IST is UTC+5:30
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_offset)

def get_ist_iso() -> str:
    """Returns IST time in ISO format."""
    return get_ist_time().isoformat()

def get_ist_strftime(fmt: str) -> str:
    """Returns formatted IST time string."""
    return get_ist_time().strftime(fmt)

import re

def parse_relative_date_to_timestamp(date_str: str) -> float:
    """Converts a relative date string ('2 days ago', '2023-10-25') to a Unix timestamp."""
    now_ts = datetime.now().timestamp()
    if not date_str:
        return now_ts - 86400 # Treat missing Naukri dates as 24 hours old so actual fresh jobs float above them

    date_str = str(date_str).lower().strip()
    
    # Try ISO
    try:
        dt = datetime.fromisoformat(date_str.replace('z', '+00:00'))
        return dt.timestamp()
    except ValueError:
        pass
        
    now = datetime.now()
    
    # Check for recent relative times
    if 'just now' in date_str or 'today' in date_str or 'hour' in date_str or 'minute' in date_str:
        return now.timestamp()
        
    # Check for days/weeks roughly
    match = re.search(r'(\d+)\s+(day|week|month|year)', date_str)
    if match:
        val = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'day':
            dt = now - timedelta(days=val)
        elif unit == 'week':
            dt = now - timedelta(weeks=val)
        elif unit == 'month':
            dt = now - timedelta(days=val * 30)
        elif unit == 'year':
            dt = now - timedelta(days=val * 365)
        else:
            dt = now
        return dt.timestamp()
        
    return 0.0
