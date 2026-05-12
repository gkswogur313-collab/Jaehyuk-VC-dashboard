import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import urllib.parse
from email.utils import parsedate_to_datetime

def fetch_google_news():
    # 1. 설정: 검색 키워드
    query = "벤처"
    
    # 최근 2주 날짜 범위 계산
    today = datetime.now()
    two_weeks_ago = today - timedelta(weeks=2)
    after_str = two_weeks_ago.strftime('%Y-%m-%d')
    
    # after: 파라미터로 2주 이내 기사만 필터링
    full_query = f"{query} after:{after_str}"
    encoded_query = urllib.parse.quote(full_query)
    
    # 구글 뉴스 RSS URL (검색어 + 날짜 필터)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'xml')
    items = soup.find_all('item')

    # 2. 중복 제거 및 날짜 파싱 후 최신순 정렬
    seen_titles = set()
    news_list = []

    for item in items:
        title = item.title.text.strip()
        main_title = title.split(' - ')[0]

        if main_title in seen_titles:
            continue
        seen_titles.add(main_title)

        link = item.link.text
        pub_date_raw = item.pubDate.text if item.pubDate else ""
        source = item.source.text if item.source else "출처 미상"

        # 날짜 파싱 (정렬용)
        try:
            pub_dt = parsedate_to_datetime(pub_date_raw)
            # timezone-naive로 변환
            pub_dt_naive = pub_dt.replace(tzinfo=None)
        except Exception:
            pub_dt_naive = datetime.min

        # 2주 이내 기사만 포함 (RSS가 after: 파라미터를 완벽히 지원하지 않을 수 있어 직접 필터링)
        if pub_dt_naive < two_weeks_ago:
            continue

        pub_date_display = pub_date_raw[:16] if pub_date_raw else "날짜 미상"

        news_list.append({
            'title': title,
            'link': link,
            'pub_dt': pub_dt_naive,
            'pub_date_display': pub_date_display,
            'source': source,
        })

        if len(news_list) >= 1000:
            break

    # 최신순 정렬
    news_list.sort(key=lambda x: x['pub_dt'], reverse=True)

    # 3. HTML 생성
    now = today.strftime('%Y-%m-%d %H:%M:%S')
    count = len(news_list)

    html_items = ""
    for news in news_list:
        html_items += f"""
            <li>
                <a href='{news["link"]}' target='_blank'>{news["title"]}</a>
                <span class="meta">{news["source"]} | {news["pub_date_display"]}</span>
            </li>
        """

    html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VC Insight Dashboard</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; padding: 20px; background-color: #f4f7f6; color: #333; }}
        .container {{ max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
        h1 {{ color: #004a99; border-bottom: 3px solid #004a99; padding-bottom: 10px; font-size: 24px; }}
        .info {{ color: #666; font-size: 0.9em; margin-bottom: 20px; display: flex; justify-content: space-between; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin-bottom: 12px; padding: 12px; border-bottom: 1px solid #eee; }}
        li:hover {{ background-color: #f9f9f9; }}
        a {{ text-decoration: none; color: #1a0dab; font-weight: bold; font-size: 1.05em; }}
        a:visited {{ color: #609; }}
        .meta {{ color: #006621; font-size: 0.85em; margin-top: 5px; display: block; }}
        .count-badge {{ background: #004a99; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📰 VC Insight: "{query}" 뉴스</h1>
        <div class="info">
            <span>업데이트: {now} | 기간: 최근 2주 ({after_str} ~ {today.strftime('%Y-%m-%d')})</span>
            <span class="count-badge">검색된 뉴스: {count}건</span>
        </div>
        <ul id="news-list">
            {html_items}
        </ul>
    </div>
</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"완료: {count}건 저장 (최근 2주, 최신순)")

if __name__ == "__main__":
    fetch_google_news()
