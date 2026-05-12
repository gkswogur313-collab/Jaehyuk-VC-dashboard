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
        return None

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

        if category is None:
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

    news_list.sort(key=lambda x: x['pub_dt'], reverse=True)

    now = today.strftime('%Y-%m-%d %H:%M:%S')
    count = len(news_list)

    html_items = ""
    for news in news_list:
        css_class = news['category'].replace('&', '')
        html_items += f"""
            <li data-category="{news['category']}">
                <a href='{news["link"]}' target='_blank'>{news["title"]}</a>
                <span class="meta">
                    <span class="category-badge cat-{css_class}">{news['category']}</span>
                    {news["source"]} | {news["pub_date_display"]}
                </span>
            </li>
        """

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>뉴스 — VC Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Malgun Gothic', sans-serif; background: #f8fafc; display: flex; min-height: 100vh; }}

        /* ── 사이드바 ── */
        .sidebar {{
            width: 200px; min-height: 100vh; background: #1e293b;
            display: flex; flex-direction: column; flex-shrink: 0;
            position: fixed; top: 0; left: 0; bottom: 0;
        }}
        .sidebar-logo {{
            padding: 24px 20px 20px;
            font-size: 15px; font-weight: bold; color: #fff;
            border-bottom: 0.5px solid #334155;
            line-height: 1.4;
        }}
        .sidebar-logo span {{ display: block; font-size: 10px; color: #64748b; font-weight: normal; margin-top: 2px; }}
        .sidebar-nav {{ padding: 12px 10px; flex: 1; }}
        .nav-item {{
            display: flex; align-items: center; gap: 10px;
            padding: 9px 12px; border-radius: 7px;
            font-size: 13px; color: #94a3b8;
            text-decoration: none; margin-bottom: 2px;
            transition: background 0.15s;
        }}
        .nav-item:hover {{ background: #273449; color: #e2e8f0; }}
        .nav-item.active {{ background: #334155; color: #fff; }}
        .nav-icon {{ font-size: 16px; }}
        .sidebar-footer {{
            padding: 14px 20px;
            font-size: 10px; color: #475569;
            border-top: 0.5px solid #334155;
        }}

        /* ── 메인 콘텐츠 ── */
        .main {{ margin-left: 200px; flex: 1; padding: 32px 36px; }}

        /* ── 헤더 ── */
        .page-header {{ margin-bottom: 24px; }}
        .page-title {{ font-size: 22px; font-weight: bold; color: #0f172a; }}
        .page-sub {{ font-size: 13px; color: #64748b; margin-top: 4px; }}

        /* ── 요약 카드 ── */
        .stat-row {{ display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }}
        .stat-card {{
            background: #fff; border: 0.5px solid #e2e8f0;
            border-radius: 10px; padding: 14px 18px; min-width: 110px;
        }}
        .stat-num {{ font-size: 24px; font-weight: bold; color: #0f172a; }}
        .stat-lbl {{ font-size: 11px; color: #94a3b8; margin-top: 2px; }}

        /* ── 필터 버튼 ── */
        .filter-bar {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }}
        .filter-btn {{
            padding: 6px 14px; border: 1px solid #cbd5e1; border-radius: 999px;
            background: #fff; color: #475569; font-size: 12px; cursor: pointer;
            font-family: 'Malgun Gothic', sans-serif; transition: all 0.15s;
        }}
        .filter-btn:hover {{ background: #f1f5f9; }}
        .filter-btn.active {{ background: #1e293b; color: #fff; border-color: #1e293b; }}
        .btn-count {{
            display: inline-block; background: rgba(0,0,0,0.08);
            border-radius: 999px; padding: 0 6px; font-size: 11px; margin-left: 3px;
        }}
        .filter-btn.active .btn-count {{ background: rgba(255,255,255,0.2); }}

        /* ── 결과 수 ── */
        .result-count {{ font-size: 12px; color: #94a3b8; margin-bottom: 10px; }}

        /* ── 뉴스 목록 ── */
        .news-list {{ list-style: none; background: #fff; border: 0.5px solid #e2e8f0; border-radius: 10px; overflow: hidden; }}
        .news-list li {{ padding: 14px 18px; border-bottom: 0.5px solid #f1f5f9; transition: background 0.1s; }}
        .news-list li:last-child {{ border-bottom: none; }}
        .news-list li:hover {{ background: #f8fafc; }}
        .news-list li.hidden {{ display: none; }}
        .news-list a {{ text-decoration: none; color: #1e40af; font-size: 14px; font-weight: 500; line-height: 1.5; }}
        .news-list a:hover {{ text-decoration: underline; }}
        .news-list a:visited {{ color: #6d28d9; }}
        .meta {{ display: flex; align-items: center; gap: 8px; margin-top: 5px; }}
        .category-badge {{
            display: inline-block; padding: 1px 8px; border-radius: 999px;
            font-size: 10px; font-weight: bold; color: #fff; white-space: nowrap;
        }}
        .cat-VC      {{ background: #1976d2; }}
        .cat-투자유치 {{ background: #388e3c; }}
        .cat-IPO     {{ background: #f57c00; }}
        .cat-MA      {{ background: #7b1fa2; }}
        .cat-분할     {{ background: #c62828; }}
        .cat-신사업   {{ background: #00838f; }}
        .meta-text {{ font-size: 11px; color: #94a3b8; }}
    </style>
</head>
<body>

    <!-- 사이드바 -->
    <aside class="sidebar">
        <div class="sidebar-logo">
            VC Dashboard
            <span>Venture Capital</span>
        </div>
        <nav class="sidebar-nav">
            <a href="index.html" class="nav-item">
                <span class="nav-icon">🏠</span> 대시보드
            </a>
            <a href="news.html" class="nav-item active">
                <span class="nav-icon">📰</span> 뉴스
            </a>
            <a href="investment.html" class="nav-item">
                <span class="nav-icon">💼</span> 출자사업
            </a>
            <a href="calendar.html" class="nav-item">
                <span class="nav-icon">📅</span> 캘린더
            </a>
        </nav>
        <div class="sidebar-footer">
            업데이트: {now}
        </div>
    </aside>

    <!-- 메인 -->
    <main class="main">
        <div class="page-header">
            <div class="page-title">Venture Capital News</div>
            <div class="page-sub">최근 2주 기사 · {after_str} ~ {today.strftime('%Y-%m-%d')} · 최신순</div>
        </div>

        <!-- 요약 카드 -->
        <div class="stat-row" id="stat-row">
            <div class="stat-card"><div class="stat-num" id="stat-전체">{count}</div><div class="stat-lbl">전체</div></div>
            <div class="stat-card"><div class="stat-num" id="stat-VC">-</div><div class="stat-lbl">VC</div></div>
            <div class="stat-card"><div class="stat-num" id="stat-투자유치">-</div><div class="stat-lbl">투자유치</div></div>
            <div class="stat-card"><div class="stat-num" id="stat-IPO">-</div><div class="stat-lbl">IPO</div></div>
            <div class="stat-card"><div class="stat-num" id="stat-MA">-</div><div class="stat-lbl">M&A</div></div>
            <div class="stat-card"><div class="stat-num" id="stat-분할">-</div><div class="stat-lbl">분할</div></div>
            <div class="stat-card"><div class="stat-num" id="stat-신사업">-</div><div class="stat-lbl">신사업</div></div>
        </div>

        <!-- 필터 -->
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

        <ul class="news-list" id="news-list">
            {html_items}
        </ul>
    </main>

    <script>
        window.onload = function() {{
            const items = document.querySelectorAll('#news-list li');
            const counts = {{}};
            items.forEach(item => {{
                const cat = item.dataset.category;
                counts[cat] = (counts[cat] || 0) + 1;
            }});
            const catMap = {{
                'VC': 'VC', '투자유치': '투자유치', 'IPO': 'IPO',
                'M&A': 'MA', '분할': '분할', '신사업': '신사업'
            }};
            let total = 0;
            Object.keys(counts).forEach(cat => {{ total += counts[cat]; }});
            document.getElementById('count-전체').textContent = total;
            Object.entries(catMap).forEach(([cat, id]) => {{
                const n = counts[cat] || 0;
                document.getElementById('count-' + id).textContent = n;
                const statEl = document.getElementById('stat-' + id);
                if (statEl) statEl.textContent = n;
            }});
            document.getElementById('stat-전체').textContent = total;
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

    with open("news.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"완료: {count}건 저장 (news.html)")

if __name__ == "__main__":
    fetch_google_news()
