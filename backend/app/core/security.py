from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()


def verify_admin_api_key(x_admin_api_key: str = Header(default="")) -> None:
    expected_key = os.getenv("ADMIN_API_KEY")

    if not expected_key or x_admin_api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid admin API key.",
        )
