import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import urllib.parse
from email.utils import parsedate_to_datetime

def fetch_google_news():
    query = "벤처 OR 스타트업 OR VC OR 투자유치 OR IPO OR 상장 OR 기업공개 OR M&A OR 인수합병 OR 인수 OR 합병 OR 분할 OR 신사업"

    today = datetime.now()
    two_weeks_ago = today - timedelta(weeks=2)
    after_str = two_weeks_ago.strftime('%Y-%m-%d')

    full_query = f"{query} after:{after_str}"
    encoded_query = urllib.parse.quote(full_query)

    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"

    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'xml')
    items = soup.find_all('item')

    # 카테고리 키워드 정의
    categories = {
        'VC':    ['VC', '스타트업', '벤처'],
        'IPO':   ['IPO', '상장', '기업공개'],
        'M&A':   ['M&A', '인수합병', '인수', '합병'],
        '투자유치': ['투자유치'],
        '분할':   ['분할'],
        '신사업':  ['신사업'],
    }

    def get_category(title):
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in title:
                    return cat
        return None  # 키워드 미해당 → 제외

    # 중복 제거 및 파싱
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

        try:
            pub_dt = parsedate_to_datetime(pub_date_raw)
            pub_dt_naive = pub_dt.replace(tzinfo=None)
        except Exception:
            pub_dt_naive = datetime.min

        if pub_dt_naive < two_weeks_ago:
            continue

        pub_date_display = pub_date_raw[:16] if pub_date_raw else "날짜 미상"
        category = get_category(title)

        if category is None:  # 키워드 미해당 기사 제외
            continue

        news_list.append({
            'title': title,
            'link': link,
            'pub_dt': pub_dt_naive,
            'pub_date_display': pub_date_display,
            'source': source,
            'category': category,
        })

        if len(news_list) >= 1000:
            break

    # 최신순 정렬
    news_list.sort(key=lambda x: x['pub_dt'], reverse=True)

    now = today.strftime('%Y-%m-%d %H:%M:%S')
    count = len(news_list)

    # 뉴스 아이템 HTML 생성 (M&A → MA로 CSS 클래스명 변환)
    html_items = ""
    for news in news_list:
        css_class = news['category'].replace('&', '')  # M&A → MA
        html_items += f"""
            <li data-category="{news['category']}">
                <a href='{news["link"]}' target='_blank'>{news["title"]}</a>
                <span class="meta">
                    <span class="category-badge cat-{css_class}">{news['category']}</span>
                    {news["source"]} | {news["pub_date_display"]}
                </span>
            </li>
        """

    html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Venture Capital News</title>
    <style>
        body {{ font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; padding: 20px; background-color: #f4f7f6; color: #333; }}
        .container {{ max-width: 900px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
        h1 {{ color: #004a99; border-bottom: 3px solid #004a99; padding-bottom: 10px; font-size: 24px; }}
        .info {{ color: #666; font-size: 0.9em; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }}
        .count-badge {{ background: #004a99; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.8em; }}
        .filter-bar {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }}
        .filter-btn {{
            padding: 6px 16px; border: 2px solid #004a99; border-radius: 20px;
            background: white; color: #004a99; font-size: 0.9em; cursor: pointer;
            font-family: 'Malgun Gothic', sans-serif; transition: all 0.2s;
        }}
        .filter-btn:hover {{ background: #e8f0fe; }}
        .filter-btn.active {{ background: #004a99; color: white; }}
        .btn-count {{
            display: inline-block; background: rgba(0,74,153,0.12);
            color: #004a99; border-radius: 10px; padding: 0 6px;
            font-size: 0.8em; margin-left: 4px;
        }}
        .filter-btn.active .btn-count {{ background: rgba(255,255,255,0.3); color: white; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin-bottom: 12px; padding: 12px; border-bottom: 1px solid #eee; }}
        li:hover {{ background-color: #f9f9f9; }}
        li.hidden {{ display: none; }}
        a {{ text-decoration: none; color: #1a0dab; font-weight: bold; font-size: 1.05em; }}
        a:visited {{ color: #609; }}
        .meta {{ color: #006621; font-size: 0.85em; margin-top: 5px; display: flex; align-items: center; gap: 8px; }}
        .category-badge {{
            display: inline-block; padding: 1px 8px; border-radius: 10px;
            font-size: 0.8em; font-weight: bold; color: white; white-space: nowrap;
        }}
        .cat-VC      {{ background: #1976d2; }}
        .cat-투자유치 {{ background: #388e3c; }}
        .cat-IPO     {{ background: #f57c00; }}
        .cat-MA      {{ background: #7b1fa2; }}
        .cat-분할     {{ background: #c62828; }}
        .cat-신사업   {{ background: #00838f; }}
        .result-count {{ font-size: 0.85em; color: #888; margin-bottom: 8px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📰 Venture Capital News</h1>
        <div class="info">
            <span>업데이트: {now} | 기간: 최근 2주 ({after_str} ~ {today.strftime('%Y-%m-%d')})</span>
            <span class="count-badge">전체 {count}건</span>
        </div>

        <div class="filter-bar">
            <button class="filter-btn active" onclick="filterNews(this, '전체')">전체 <span class="btn-count" id="count-전체"></span></button>
            <button class="filter-btn" onclick="filterNews(this, 'VC')">VC <span class="btn-count" id="count-VC"></span></button>
            <button class="filter-btn" onclick="filterNews(this, '투자유치')">투자유치 <span class="btn-count" id="count-투자유치"></span></button>
            <button class="filter-btn" onclick="filterNews(this, 'IPO')">IPO <span class="btn-count" id="count-IPO"></span></button>
            <button class="filter-btn" onclick="filterNews(this, 'M&A')">M&amp;A <span class="btn-count" id="count-MA"></span></button>
            <button class="filter-btn" onclick="filterNews(this, '분할')">분할 <span class="btn-count" id="count-분할"></span></button>
            <button class="filter-btn" onclick="filterNews(this, '신사업')">신사업 <span class="btn-count" id="count-신사업"></span></button>
        </div>

        <div class="result-count" id="result-count">전체 {count}건 표시 중</div>

        <ul id="news-list">
            {html_items}
        </ul>
    </div>

    <script>
        window.onload = function() {{
            const items = document.querySelectorAll('#news-list li');
            const counts = {{}};
            let total = 0;
            items.forEach(item => {{
                const cat = item.dataset.category;
                counts[cat] = (counts[cat] || 0) + 1;
                total++;
            }});
            document.getElementById('count-전체').textContent = total;
            document.getElementById('count-VC').textContent = counts['VC'] || 0;
            document.getElementById('count-투자유치').textContent = counts['투자유치'] || 0;
            document.getElementById('count-IPO').textContent = counts['IPO'] || 0;
            document.getElementById('count-MA').textContent = counts['M&A'] || 0;
            document.getElementById('count-분할').textContent = counts['분할'] || 0;
            document.getElementById('count-신사업').textContent = counts['신사업'] || 0;
        }};

        function filterNews(btn, category) {{
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const items = document.querySelectorAll('#news-list li');
            let visibleCount = 0;

            items.forEach(item => {{
                if (category === '전체' || item.dataset.category === category) {{
                    item.classList.remove('hidden');
                    visibleCount++;
                }} else {{
                    item.classList.add('hidden');
                }}
            }});

            const label = category === '전체' ? '전체' : '[' + category + ']';
            document.getElementById('result-count').textContent = label + ' ' + visibleCount + '건 표시 중';
        }}
    </script>
</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"완료: {count}건 저장 (최근 2주, 최신순, 카테고리 필터 적용)")

if __name__ == "__main__":
    fetch_google_news()
