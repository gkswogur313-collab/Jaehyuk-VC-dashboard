"""
crawl_notice.py
KVCA 공지사항 전체 수집 → data/notice.json 저장
GitHub Actions에서 주기적으로 실행됩니다.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime

BASE_URL = "https://www.kvca.or.kr/Program/board/list.html"
PARAMS_BASE = {
    "a_gb": "board",
    "a_cd": "5",
    "a_item": "0",
    "sm": "3_1",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "notice.json")


def parse_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tbody = soup.find("tbody")
    if not tbody:
        return []

    rows = []
    for tr in tbody.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue

        no_raw = tds[0].get_text(strip=True)
        is_pinned = "[공지]" in no_raw
        no_num = None if is_pinned else (int(no_raw) if no_raw.isdigit() else None)

        cat = tds[1].get_text(strip=True)

        title_td = tds[2]
        a_tag = title_td.find("a")
        title = a_tag.get_text(strip=True) if a_tag else title_td.get_text(strip=True)
        href = a_tag["href"] if a_tag and a_tag.get("href") else ""
        if href and not href.startswith("http"):
            href = "https://www.kvca.or.kr" + href

        date = tds[3].get_text(strip=True)
        views = 0
        if len(tds) >= 5:
            views_text = tds[4].get_text(strip=True).replace(",", "")
            views = int(views_text) if views_text.isdigit() else 0

        if title and date:
            rows.append({
                "no": no_num,
                "isPinned": is_pinned,
                "cat": cat,
                "title": title,
                "link": href,
                "date": date,
                "views": views,
            })
    return rows


def get_total_pages(html: str) -> int:
    """마지막 페이지 번호 파싱"""
    soup = BeautifulSoup(html, "html.parser")
    # 페이지네이션에서 가장 큰 숫자 추출
    paging = soup.find("div", class_="paging") or soup.find("div", class_="board_paging")
    max_page = 1
    if paging:
        for a in paging.find_all("a"):
            href = a.get("href", "")
            if "page=" in href:
                try:
                    p = int(href.split("page=")[-1].split("&")[0])
                    max_page = max(max_page, p)
                except ValueError:
                    pass
    return max_page


def crawl_all() -> list[dict]:
    all_items = []

    # 1페이지 먼저 가져와서 전체 페이지 수 파악
    resp = requests.get(BASE_URL, params={**PARAMS_BASE, "page": 1}, headers=HEADERS, timeout=15)
    resp.encoding = "utf-8"
    total_pages = get_total_pages(resp.text)
    items = parse_page(resp.text)
    all_items.extend(items)
    print(f"[1/{total_pages}] {len(items)}건")

    for page in range(2, total_pages + 1):
        try:
            resp = requests.get(BASE_URL, params={**PARAMS_BASE, "page": page}, headers=HEADERS, timeout=15)
            resp.encoding = "utf-8"
            items = parse_page(resp.text)
            all_items.extend(items)
            print(f"[{page}/{total_pages}] {len(items)}건")
            time.sleep(0.3)  # 서버 부하 방지
        except Exception as e:
            print(f"[{page}] 오류: {e}")
            time.sleep(1)

    return all_items


def main():
    print(f"크롤링 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    data = crawl_all()
    print(f"총 {len(data)}건 수집 완료")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(data),
        "items": data,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
