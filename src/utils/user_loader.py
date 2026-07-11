import json
from pathlib import Path
from typing import Any, Dict, Optional

FIXTURES_USERS_DIR = Path(__file__).parent.parent.parent / "fixtures" / "users"

def load_user_portfolio(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Scans the fixtures/users directory to locate and parse 
    the JSON file matching the provided user_id string.
    """
    if not FIXTURES_USERS_DIR.exists():
        return None

    for json_path in FIXTURES_USERS_DIR.glob("*.json"):
        try:
            with open(json_path, encoding="utf-8") as file:
                profile_data = json.load(file)
                if profile_data.get("user_id") == user_id:
                    return profile_data
        except (json.JSONDecodeError, IOError):
            continue

    return None