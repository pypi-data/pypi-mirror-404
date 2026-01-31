# krx_hj3415/provider/krx300_samsungfund_excel.py
from __future__ import annotations

import random
import time
import pandas as pd
import requests
from datetime import datetime, timedelta, timezone
from io import BytesIO

from domain_hj3415.common.time import utcnow
from krx_hj3415.domain.types import CodeItem


FUND_ID = "2ETFA4"
BASE_URL = "https://www.samsungfund.com/excel_pdf.do"


def _looks_like_excel(content: bytes) -> bool:
    # xls(ole) or xlsx(zip) 대충 체크
    return content.startswith(b"\xd0\xcf\x11\xe0") or content.startswith(b"PK\x03\x04")


def find_valid_url(*, max_days: int = 15, timeout: int = 8) -> tuple[str, datetime]:
    for delta in range(1, max_days + 1):
        day = (utcnow() - timedelta(days=delta)).astimezone(timezone.utc)
        date_str = day.strftime("%Y%m%d")
        url = f"{BASE_URL}?fId={FUND_ID}&gijunYMD={date_str}"

        try:
            r = requests.get(url, timeout=timeout)
            time.sleep(random.uniform(1.2, 2.2))

            if r.status_code != 200:
                continue

            content = r.content or b""
            if len(content) < 2000:
                continue
            if not _looks_like_excel(content):
                continue

            return url, day
        except Exception:
            continue

    raise RuntimeError("유효한 KRX300 엑셀 파일을 찾지 못했습니다.")


def download_excel_bytes(*, max_days: int = 15) -> tuple[bytes, datetime, str]:
    url, asof_day = find_valid_url(max_days=max_days)
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.content, asof_day, url


def parse_krx300_items(excel_bytes: bytes, *, asof: datetime) -> list[CodeItem]:
    # 네가 쓰던 조건: usecols B:I, skiprows 2
    df = pd.read_excel(BytesIO(excel_bytes), usecols="B:I", skiprows=2)  # type: ignore

    # 방어: 컬럼명이 조금 바뀌어도 대응하려면 rename 전략을 쓰는 게 좋음
    # 일단 네 기존대로 "종목코드", "종목명" 기준으로 진행
    if "종목코드" not in df.columns or "종목명" not in df.columns:
        raise ValueError(f"Unexpected columns: {list(df.columns)}")

    # 6자리만
    df = df[df["종목코드"].astype(str).str.fullmatch(r"\d{6}", na=False)]

    # 원화예금 제거
    df = df[df["종목명"] != "원화예금"]

    items: list[CodeItem] = []
    for code, name in zip(df["종목코드"].astype(str), df["종목명"].astype(str)):
        items.append(CodeItem(code=code, name=name, asof=asof))
    return items


def fetch_krx300_items(*, max_days: int = 15) -> tuple[datetime, list[CodeItem]]:
    excel_bytes, asof_day, _url = download_excel_bytes(max_days=max_days)
    items = parse_krx300_items(excel_bytes, asof=asof_day)
    return asof_day, items
