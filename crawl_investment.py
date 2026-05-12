import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

def fetch_kvca():
    """한국벤처캐피탈협회 출자공고"""
    url = "https://www.kvca.or.kr/Program/invest/list.html?a_gb=board&a_cd=8&a_item=0&sm=2_2_2"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table tr')[1:]  # 헤더 제외
        items = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 4:
                continue
            a_tag = cols[2].find('a')
            title = a_tag.text.strip() if a_tag else cols[2].text.strip()
            link = "https://www.kvca.or.kr" + a_tag['href'] if a_tag and a_tag.get('href') else url
            lp = cols[1].text.strip()
            date_str = cols[3].text.strip()
            deadline = cols[4].text.strip() if len(cols) > 4 else ''
            items.append({
                'source': 'KVCA',
                'source_label': '한국벤처캐피탈협회',
                'title': title,
                'link': link,
                'lp': lp,
                'date': date_str,
                'deadline': deadline,
                'category': '',
            })
        return items
    except Exception as e:
        print(f"KVCA 오류: {e}")
        return []

def fetch_kgrowth():
    """한국성장금융"""
    url = "https://www.kgrowth.or.kr/notice.asp?str_type=1&tab=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table tr')
        items = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 3:
                continue
            num_text = cols[0].text.strip()
            # 공지(이미지) 행 제외, 숫자 번호만
            if not num_text.isdigit():
                continue
            a_tag = cols[1].find('a')
            title = a_tag.text.strip() if a_tag else cols[1].text.strip()
            # 이미지 태그 텍스트 제거
            title = ' '.join(title.split())
            href = a_tag['href'] if a_tag and a_tag.get('href') else ''
            link = "https://www.kgrowth.or.kr/" + href.lstrip('/') if href else url
            date_str = cols[2].text.strip() if len(cols) > 2 else ''
            items.append({
                'source': 'KGROWTH',
                'source_label': '한국성장금융',
                'title': title,
                'link': link,
                'lp': '',
                'date': date_str,
                'deadline': '',
                'category': '',
            })
        return items
    except Exception as e:
        print(f"한국성장금융 오류: {e}")
        return []

def fetch_kvic():
    """한국벤처투자"""
    url = "https://www.kvic.or.kr/notice/kvic-notice/investment-business-notice"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table tr')[1:]
        items = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 4:
                continue
            num_text = cols[0].text.strip()
            if not num_text.isdigit():
                continue
            category = cols[1].text.strip()
            a_tag = cols[3].find('a')
            title = a_tag.text.strip() if a_tag else cols[3].text.strip()
            # javascript: 링크는 원본 페이지로
            href = a_tag['href'] if a_tag else ''
            link = url if href.startswith('javascript') else href
            date_str = cols[4].text.strip() if len(cols) > 4 else ''
            items.append({
                'source': 'KVIC',
                'source_label': '한국벤처투자',
                'title': title,
                'link': link,
                'lp': '',
                'date': date_str,
                'deadline': '',
                'category': category,
            })
        return items
    except Exception as e:
        print(f"한국벤처투자 오류: {e}")
        return []

def parse_date(date_str):
    for fmt in ['%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d']:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    return datetime.min

def all_rows(items):
    rows = ''
    for i, item in enumerate(items):
        rows += f"""<tr>
                            <td class="td-num">{i+1}</td>
                            <td class="td-lp">{item['source_label']}</td>
                            <td class="td-title"><a href="{item['link']}" target="_blank">{item['title']}</a></td>
                            <td class="td-date">{item['date']}</td>
                        </tr>"""
    return rows

def build_html(all_items, now_str):
    kvca = [i for i in all_items if i['source'] == 'KVCA']
    kgrowth = [i for i in all_items if i['source'] == 'KGROWTH']
    kvic = [i for i in all_items if i['source'] == 'KVIC']

    def kvca_rows(items):
        rows = ''
        for item in items:
            rows += f"""<tr>
                <td class="td-lp">{item['lp']}</td>
                <td class="td-title"><a href="{item['link']}" target="_blank">{item['title']}</a></td>
                <td class="td-date">{item['date']}</td>
                <td class="td-date">{item['deadline']}</td>
            </tr>"""
        return rows

    def kgrowth_rows(items):
        rows = ''
        for i, item in enumerate(items, 1):
            rows += f"""<tr>
                <td class="td-num">{i}</td>
                <td class="td-title"><a href="{item['link']}" target="_blank">{item['title']}</a></td>
                <td class="td-date">{item['date']}</td>
            </tr>"""
        return rows

    def kvic_rows(items):
        rows = ''
        for i, item in enumerate(items, 1):
            cat = item['category'].replace('[','').replace(']','')
            rows += f"""<tr>
                <td class="td-num">{i}</td>
                <td class="td-cat"><span class="cat-badge">{cat}</span></td>
                <td class="td-title"><a href="{item['link']}" target="_blank">{item['title']}</a></td>
                <td class="td-date">{item['date']}</td>
            </tr>"""
        return rows

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>출자사업 — VC Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Malgun Gothic', sans-serif; background: #f8fafc; display: flex; min-height: 100vh; }}

        /* 사이드바 */
        .sidebar {{
            width: 200px; min-height: 100vh; background: #1e293b;
            display: flex; flex-direction: column; flex-shrink: 0;
            position: fixed; top: 0; left: 0; bottom: 0;
        }}
        .sidebar-logo {{
            padding: 24px 20px 20px;
            font-size: 15px; font-weight: bold; color: #fff;
            border-bottom: 0.5px solid #334155; line-height: 1.4;
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
            padding: 14px 20px; font-size: 10px; color: #475569;
            border-top: 0.5px solid #334155;
        }}

        /* 메인 */
        .main {{ margin-left: 200px; flex: 1; padding: 32px 36px; }}
        .page-header {{ margin-bottom: 24px; }}
        .page-title {{ font-size: 22px; font-weight: bold; color: #0f172a; }}
        .page-sub {{ font-size: 13px; color: #64748b; margin-top: 4px; }}

        /* 기관 탭 버튼 */
        .tab-bar {{ display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }}
        .tab-btn {{
            padding: 8px 20px; border-radius: 8px; border: 1.5px solid #cbd5e1;
            background: #fff; color: #475569; font-size: 13px; font-weight: 500;
            cursor: pointer; font-family: 'Malgun Gothic', sans-serif;
            transition: all 0.15s;
        }}
        .tab-btn:hover {{ border-color: #94a3b8; background: #f8fafc; }}
        .tab-btn.active {{ background: #1e293b; color: #fff; border-color: #1e293b; }}
        .tab-count {{
            display: inline-block; background: rgba(255,255,255,0.2);
            border-radius: 999px; padding: 0 7px; font-size: 11px; margin-left: 4px;
        }}
        .tab-btn:not(.active) .tab-count {{
            background: rgba(0,0,0,0.07); color: #64748b;
        }}

        /* 패널 */
        .panel {{ display: none; }}
        .panel.active {{ display: block; }}

        /* 패널 헤더 */
        .panel-header {{
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 12px;
        }}
        .panel-title {{ font-size: 15px; font-weight: bold; color: #0f172a; }}
        .panel-link {{
            font-size: 12px; color: #3b82f6; text-decoration: none;
        }}
        .panel-link:hover {{ text-decoration: underline; }}
        .panel-count {{ font-size: 12px; color: #94a3b8; }}

        /* 테이블 공통 */
        .tbl-wrap {{
            background: #fff; border: 0.5px solid #e2e8f0;
            border-radius: 10px; overflow: hidden;
        }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        thead {{ background: #f8fafc; }}
        th {{
            padding: 11px 14px; text-align: left; font-size: 12px;
            color: #64748b; font-weight: 600; border-bottom: 0.5px solid #e2e8f0;
        }}
        td {{ padding: 11px 14px; border-bottom: 0.5px solid #f1f5f9; vertical-align: middle; }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover td {{ background: #f8fafc; }}

        .td-num {{ color: #94a3b8; width: 50px; text-align: center; }}
        .td-lp {{ width: 140px; color: #475569; font-size: 12px; }}
        .td-title a {{ color: #1e40af; text-decoration: none; line-height: 1.5; }}
        .td-title a:hover {{ text-decoration: underline; }}
        .td-title a:visited {{ color: #6d28d9; }}
        .td-date {{ width: 100px; color: #94a3b8; font-size: 12px; white-space: nowrap; }}
        .td-cat {{ width: 90px; }}

        .cat-badge {{
            display: inline-block; padding: 2px 8px; border-radius: 999px;
            font-size: 10px; font-weight: 600;
            background: #eff6ff; color: #1d4ed8;
        }}

        .update-info {{ font-size: 11px; color: #94a3b8; margin-top: 12px; text-align: right; }}
    </style>
</head>
<body>

    <aside class="sidebar">
        <div class="sidebar-logo">
            VC Dashboard
            <span>Venture Capital</span>
        </div>
        <nav class="sidebar-nav">
            <a href="index.html" class="nav-item"><span class="nav-icon">🏠</span> 대시보드</a>
            <a href="news.html" class="nav-item"><span class="nav-icon">📰</span> 뉴스</a>
            <a href="investment.html" class="nav-item active"><span class="nav-icon">💼</span> 출자사업</a>
            <a href="calendar.html" class="nav-item"><span class="nav-icon">📅</span> 캘린더</a>
        </nav>
        <div class="sidebar-footer">업데이트: {now_str}</div>
    </aside>

    <main class="main">
        <div class="page-header">
            <div class="page-title">출자사업 공고</div>
            <div class="page-sub">주요 기관의 출자사업 공고를 공고일 기준 최신순으로 정리합니다.</div>
        </div>

        <div class="tab-bar">
            <button class="tab-btn active" onclick="switchTab(this, 'all')">
                전체 <span class="tab-count" id="cnt-all">{len(all_items)}</span>
            </button>
            <button class="tab-btn" onclick="switchTab(this, 'kvca')">
                한국벤처캐피탈협회 <span class="tab-count" id="cnt-kvca">{len(kvca)}</span>
            </button>
            <button class="tab-btn" onclick="switchTab(this, 'kgrowth')">
                한국성장금융 <span class="tab-count" id="cnt-kgrowth">{len(kgrowth)}</span>
            </button>
            <button class="tab-btn" onclick="switchTab(this, 'kvic')">
                한국벤처투자 <span class="tab-count" id="cnt-kvic">{len(kvic)}</span>
            </button>
        </div>

        <!-- 전체 탭 -->
        <div class="panel active" id="panel-all">
            <div class="panel-header">
                <span class="panel-title">전체 공고</span>
                <span class="panel-count">총 {len(all_items)}건 · 공고일 최신순</span>
            </div>
            <div class="tbl-wrap">
                <table>
                    <thead>
                        <tr>
                            <th style="width:50px">번호</th>
                            <th style="width:110px">기관</th>
                            <th>공고명</th>
                            <th style="width:100px">공고일</th>
                        </tr>
                    </thead>
                    <tbody>{all_rows(all_items)}</tbody>
                </table>
            </div>
        </div>

        <!-- KVCA 탭 -->
        <div class="panel" id="panel-kvca">
            <div class="panel-header">
                <span class="panel-title">한국벤처캐피탈협회 출자공고</span>
                <a class="panel-link" href="https://www.kvca.or.kr/Program/invest/list.html?a_gb=board&a_cd=8&a_item=0&sm=2_2_2" target="_blank">원본 사이트 바로가기 →</a>
            </div>
            <div class="tbl-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>LP명</th>
                            <th>공고명</th>
                            <th style="width:100px">공고일</th>
                            <th style="width:100px">신청기한</th>
                        </tr>
                    </thead>
                    <tbody>{kvca_rows(kvca)}</tbody>
                </table>
            </div>
        </div>

        <!-- 한국성장금융 탭 -->
        <div class="panel" id="panel-kgrowth">
            <div class="panel-header">
                <span class="panel-title">한국성장금융 출자사업공고</span>
                <a class="panel-link" href="https://www.kgrowth.or.kr/notice.asp" target="_blank">원본 사이트 바로가기 →</a>
            </div>
            <div class="tbl-wrap">
                <table>
                    <thead>
                        <tr>
                            <th style="width:50px">번호</th>
                            <th>공고명</th>
                            <th style="width:100px">작성일</th>
                        </tr>
                    </thead>
                    <tbody>{kgrowth_rows(kgrowth)}</tbody>
                </table>
            </div>
        </div>

        <!-- 한국벤처투자 탭 -->
        <div class="panel" id="panel-kvic">
            <div class="panel-header">
                <span class="panel-title">한국벤처투자 출자사업공지</span>
                <a class="panel-link" href="https://www.kvic.or.kr/notice/kvic-notice/investment-business-notice" target="_blank">원본 사이트 바로가기 →</a>
            </div>
            <div class="tbl-wrap">
                <table>
                    <thead>
                        <tr>
                            <th style="width:50px">번호</th>
                            <th style="width:90px">카테고리</th>
                            <th>제목</th>
                            <th style="width:100px">날짜</th>
                        </tr>
                    </thead>
                    <tbody>{kvic_rows(kvic)}</tbody>
                </table>
            </div>
        </div>

        <div class="update-info">마지막 업데이트: {now_str}</div>
    </main>

    <script>
        function switchTab(btn, panel) {{
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('panel-' + panel).classList.add('active');
        }}
    </script>
</body>
</html>
"""
    return html

def main():
    print("크롤링 시작...")
    kvca = fetch_kvca()
    print(f"KVCA: {len(kvca)}건")
    kgrowth = fetch_kgrowth()
    print(f"한국성장금융: {len(kgrowth)}건")
    kvic = fetch_kvic()
    print(f"한국벤처투자: {len(kvic)}건")

    all_items = kvca + kgrowth + kvic
    # 공고일 기준 최신순 정렬
    all_items.sort(key=lambda x: parse_date(x['date']), reverse=True)

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html = build_html(all_items, now_str)

    with open("investment.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"완료: investment.html 생성 (총 {len(all_items)}건)")

if __name__ == "__main__":
    main()
