import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re

def fetch_kvca():
    base_url = "https://www.kvca.or.kr/Program/invest/list.html"
    headers = {'User-Agent': 'Mozilla/5.0'}
    items = []
    page = 1

    while True:
        url = f"{base_url}?a_gb=board&a_cd=8&a_item=0&sm=2_2_2&keyfield=&key=&page={page}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select('table tr')[1:]
            found = False
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue
                a_tag = cols[2].find('a')
                if not a_tag:
                    continue
                found = True
                title = a_tag.text.strip()
                raw_href = a_tag.get('href', '')
                po_match = re.search(r'po_no=(\d+)', raw_href)
                if po_match:
                    link = f"https://www.kvca.or.kr/Program/invest/listbody.html?a_gb=board&a_cd=8&a_item=0&sm=2_2_2&page={page}&po_no={po_match.group(1)}"
                elif raw_href.startswith('http'):
                    link = raw_href
                elif raw_href.startswith('/'):
                    link = "https://www.kvca.or.kr" + raw_href
                else:
                    link = base_url
                lp = cols[1].text.strip()
                date_str = cols[3].text.strip()
                deadline = cols[4].text.strip() if len(cols) > 4 else ''
                items.append({
                    'source': 'KVCA', 'source_label': '한국벤처캐피탈협회',
                    'title': title, 'link': link, 'lp': lp,
                    'date': date_str, 'deadline': deadline, 'category': '',
                })
            if not found:
                break
            paging_nums = [int(a.text.strip()) for a in soup.find_all('a') if a.text.strip().isdigit()]
            if not paging_nums or page >= max(paging_nums):
                break
            page += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"KVCA 페이지 {page} 오류: {e}")
            break
    return items

def fetch_kgrowth():
    headers = {'User-Agent': 'Mozilla/5.0'}
    items = []
    page = 1
    while True:
        url = f"https://www.kgrowth.or.kr/notice.asp?str_type=1&tab=1&page={page}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.encoding = 'euc-kr'
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select('table tr')
            found = False
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3:
                    continue
                num_text = cols[0].text.strip()
                if not num_text.isdigit():
                    continue
                found = True
                a_tag = cols[1].find('a')
                title = ' '.join((a_tag.text.strip() if a_tag else cols[1].text.strip()).split())
                href = a_tag['href'] if a_tag and a_tag.get('href') else ''
                link = "https://www.kgrowth.or.kr/" + href.lstrip('/') if href else "https://www.kgrowth.or.kr/notice.asp"
                date_str = cols[2].text.strip()
                items.append({
                    'source': 'KGROWTH', 'source_label': '한국성장금융',
                    'title': title, 'link': link, 'lp': '',
                    'date': date_str, 'deadline': '', 'category': '',
                })
            if not found:
                break
            page_links = [a.text.strip() for a in soup.find_all('a') if a.text.strip().isdigit()]
            if str(page + 1) not in page_links:
                break
            page += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"한국성장금융 페이지 {page} 오류: {e}")
            break
    return items

def fetch_kvic():
    base_url = "https://www.kvic.or.kr/notice/kvic-notice/investment-business-notice"
    headers = {'User-Agent': 'Mozilla/5.0'}
    items = []
    seen_nums = set()

    def parse_page(soup):
        rows = soup.select('table tr')[1:]
        found = False
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 4:
                continue
            num_text = cols[0].text.strip()
            if not num_text.isdigit() or num_text in seen_nums:
                continue
            seen_nums.add(num_text)
            found = True
            category = cols[1].text.strip().replace('[', '').replace(']', '')
            a_tag = cols[3].find('a')
            title = a_tag.text.strip() if a_tag else cols[3].text.strip()
            href = a_tag.get('href', '') if a_tag else ''
            seq_match = re.search(r'board_view\((\d+)\)', href)
            if seq_match:
                link = f"{base_url}?pageNo=1&searchCategory=&searchType=all&searchWord=&id={seq_match.group(1)}"
            else:
                link = base_url
            date_str = cols[4].text.strip() if len(cols) > 4 else ''
            items.append({
                'source': 'KVIC', 'source_label': '한국벤처투자',
                'title': title, 'link': link, 'lp': '',
                'date': date_str, 'deadline': '', 'category': category,
            })
        return found

    try:
        res = requests.get(base_url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        parse_page(soup)

        last_page = 1
        last_btn = soup.find('a', title=lambda t: t and '마지막' in t)
        if last_btn:
            m = re.search(r"goPage\('(\d+)'\)", str(last_btn))
            if m:
                last_page = int(m.group(1))
        print(f"한국벤처투자 총 페이지: {last_page}")

        for pg in range(2, last_page + 1):
            try:
                url = f"{base_url}?pageNo={pg}&searchCategory=&searchType=all&searchWord="
                res = requests.get(url, headers=headers, timeout=10)
                res.encoding = 'utf-8'
                pg_soup = BeautifulSoup(res.text, 'html.parser')
                if not parse_page(pg_soup):
                    break
                time.sleep(0.3)
            except Exception as e:
                print(f"한국벤처투자 페이지 {pg} 오류: {e}")
                break
    except Exception as e:
        print(f"한국벤처투자 오류: {e}")
    return items

def parse_date(date_str):
    for fmt in ['%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d']:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    return datetime.min

def kvca_rows(items):
    rows = ''
    for item in items:
        rows += f'<tr><td class="td-lp">{item["lp"]}</td><td class="td-title"><a href="{item["link"]}" target="_blank">{item["title"]}</a></td><td class="td-date">{item["date"]}</td><td class="td-date">{item["deadline"]}</td></tr>\n'
    return rows

def kgrowth_rows(items):
    rows = ''
    for i, item in enumerate(items, 1):
        rows += f'<tr><td class="td-num">{i}</td><td class="td-title"><a href="{item["link"]}" target="_blank">{item["title"]}</a></td><td class="td-date">{item["date"]}</td></tr>\n'
    return rows

def kvic_rows(items):
    rows = ''
    for i, item in enumerate(items, 1):
        cat = item['category'].replace('[', '').replace(']', '')
        rows += f'<tr><td class="td-num">{i}</td><td class="td-cat"><span class="cat-badge">{cat}</span></td><td class="td-title"><a href="{item["link"]}" target="_blank">{item["title"]}</a></td><td class="td-date">{item["date"]}</td></tr>\n'
    return rows

# JS를 f-string 밖에서 별도 변수로 선언 (중괄호 충돌 방지)
JS_CODE = """
    <script>
        var currentPanel = 'kvca';

        function switchTab(btn, panel) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('panel-' + panel).classList.add('active');
            currentPanel = panel;
            doSearch();
        }

        function doSearch() {
            var keyword = document.getElementById('search-input').value.trim().toLowerCase();
            var searchAll = document.getElementById('search-all').checked;
            var clearBtn = document.getElementById('search-clear');
            var resultCount = document.getElementById('search-result-count');

            clearBtn.style.display = keyword ? 'inline-block' : 'none';

            if (searchAll && keyword) {
                document.querySelectorAll('.panel').forEach(p => p.classList.add('active'));
            } else {
                document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
                document.getElementById('panel-' + currentPanel).classList.add('active');
            }

            var totalVisible = 0;
            var panelsToSearch = (searchAll && keyword)
                ? Array.from(document.querySelectorAll('.panel'))
                : [document.getElementById('panel-' + currentPanel)];

            panelsToSearch.forEach(function(panel) {
                var rows = panel.querySelectorAll('tbody tr');
                var panelVisible = 0;
                rows.forEach(function(row) {
                    // 하이라이트 초기화
                    row.querySelectorAll('.highlight').forEach(function(el) {
                        var text = document.createTextNode(el.textContent);
                        el.parentNode.replaceChild(text, el);
                    });
                    if (!keyword) {
                        row.classList.remove('hidden');
                        panelVisible++;
                        return;
                    }
                    var titleTd = row.querySelector('.td-title');
                    var lpTd = row.querySelector('.td-lp');
                    var titleText = titleTd ? titleTd.textContent.toLowerCase() : '';
                    var lpText = lpTd ? lpTd.textContent.toLowerCase() : '';
                    if (titleText.includes(keyword) || lpText.includes(keyword)) {
                        row.classList.remove('hidden');
                        panelVisible++;
                        if (titleTd) {
                            var a = titleTd.querySelector('a');
                            if (a) {
                                var escaped = keyword.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
                                var re = new RegExp('(' + escaped + ')', 'gi');
                                a.innerHTML = a.textContent.replace(re, '<span class="highlight">$1</span>');
                            }
                        }
                    } else {
                        row.classList.add('hidden');
                    }
                });
                totalVisible += panelVisible;
            });

            if (keyword) {
                var scope = searchAll ? '전체 기관' : '현재 탭';
                resultCount.textContent = scope + ' 검색 결과: ' + totalVisible + '건';
            } else {
                resultCount.textContent = '';
            }
        }

        function clearSearch() {
            document.getElementById('search-input').value = '';
            document.getElementById('search-all').checked = false;
            doSearch();
        }
    </script>
"""

def build_html(kvca, kgrowth, kvic, now_str):
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>출자사업 — VC Dashboard</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: 'Malgun Gothic', sans-serif; background: #f8fafc; display: flex; min-height: 100vh; }}
        .sidebar {{ width: 200px; min-height: 100vh; background: #1e293b; display: flex; flex-direction: column; flex-shrink: 0; position: fixed; top: 0; left: 0; bottom: 0; }}
        .sidebar-logo {{ padding: 24px 20px 20px; font-size: 15px; font-weight: bold; color: #fff; border-bottom: 0.5px solid #334155; line-height: 1.4; }}
        .sidebar-logo span {{ display: block; font-size: 10px; color: #64748b; font-weight: normal; margin-top: 2px; }}
        .sidebar-nav {{ padding: 12px 10px; flex: 1; }}
        .nav-item {{ display: flex; align-items: center; gap: 10px; padding: 9px 12px; border-radius: 7px; font-size: 13px; color: #94a3b8; text-decoration: none; margin-bottom: 2px; transition: background 0.15s; }}
        .nav-item:hover {{ background: #273449; color: #e2e8f0; }}
        .nav-item.active {{ background: #334155; color: #fff; }}
        .nav-icon {{ font-size: 16px; }}
        .sidebar-footer {{ padding: 14px 20px; font-size: 10px; color: #475569; border-top: 0.5px solid #334155; }}
        .main {{ margin-left: 200px; flex: 1; padding: 32px 36px; }}
        .page-header {{ margin-bottom: 24px; }}
        .page-title {{ font-size: 22px; font-weight: bold; color: #0f172a; }}
        .page-sub {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
        .tab-bar {{ display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }}
        .tab-btn {{ padding: 8px 20px; border-radius: 8px; border: 1.5px solid #cbd5e1; background: #fff; color: #475569; font-size: 13px; font-weight: 500; cursor: pointer; font-family: 'Malgun Gothic', sans-serif; transition: all 0.15s; }}
        .tab-btn:hover {{ border-color: #94a3b8; background: #f8fafc; }}
        .tab-btn.active {{ background: #1e293b; color: #fff; border-color: #1e293b; }}
        .tab-count {{ display: inline-block; background: rgba(255,255,255,0.2); border-radius: 999px; padding: 0 7px; font-size: 11px; margin-left: 4px; }}
        .tab-btn:not(.active) .tab-count {{ background: rgba(0,0,0,0.07); color: #64748b; }}
        .search-bar {{ display: flex; gap: 8px; margin-bottom: 12px; align-items: center; flex-wrap: wrap; }}
        .search-input {{ flex: 1; max-width: 400px; padding: 8px 14px; border: 1.5px solid #cbd5e1; border-radius: 8px; font-size: 13px; font-family: 'Malgun Gothic', sans-serif; outline: none; transition: border-color 0.15s; }}
        .search-input:focus {{ border-color: #1e293b; }}
        .search-btn {{ padding: 8px 16px; border-radius: 8px; border: 1.5px solid #1e293b; background: #1e293b; color: #fff; font-size: 13px; cursor: pointer; font-family: 'Malgun Gothic', sans-serif; }}
        .search-btn:hover {{ background: #334155; }}
        .search-clear {{ padding: 8px 12px; border-radius: 8px; border: 1.5px solid #cbd5e1; background: #fff; color: #64748b; font-size: 12px; cursor: pointer; font-family: 'Malgun Gothic', sans-serif; display: none; }}
        .search-all-label {{ font-size: 12px; color: #64748b; display: flex; align-items: center; gap: 5px; cursor: pointer; }}
        .search-result-count {{ font-size: 12px; color: #94a3b8; margin-bottom: 10px; min-height: 18px; }}
        .panel {{ display: none; }}
        .panel.active {{ display: block; }}
        .panel-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }}
        .panel-title {{ font-size: 15px; font-weight: bold; color: #0f172a; }}
        .panel-link {{ font-size: 12px; color: #3b82f6; text-decoration: none; }}
        .panel-link:hover {{ text-decoration: underline; }}
        .panel-count {{ font-size: 12px; color: #94a3b8; }}
        .tbl-wrap {{ background: #fff; border: 0.5px solid #e2e8f0; border-radius: 10px; overflow: hidden; margin-bottom: 24px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        thead {{ background: #f8fafc; }}
        th {{ padding: 11px 14px; text-align: left; font-size: 12px; color: #64748b; font-weight: 600; border-bottom: 0.5px solid #e2e8f0; }}
        td {{ padding: 11px 14px; border-bottom: 0.5px solid #f1f5f9; vertical-align: middle; }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover td {{ background: #f8fafc; }}
        tr.hidden {{ display: none; }}
        .td-num {{ color: #94a3b8; width: 50px; text-align: center; }}
        .td-lp {{ width: 140px; color: #475569; font-size: 12px; }}
        .td-title a {{ color: #1e40af; text-decoration: none; line-height: 1.5; }}
        .td-title a:hover {{ text-decoration: underline; }}
        .td-title a:visited {{ color: #6d28d9; }}
        .td-date {{ width: 100px; color: #94a3b8; font-size: 12px; white-space: nowrap; }}
        .td-cat {{ width: 90px; }}
        .cat-badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 10px; font-weight: 600; background: #eff6ff; color: #1d4ed8; }}
        .highlight {{ background: #fef9c3; border-radius: 2px; padding: 0 1px; }}
        .update-info {{ font-size: 11px; color: #94a3b8; margin-top: 12px; text-align: right; }}
    </style>
</head>
<body>
    <aside class="sidebar">
        <div class="sidebar-logo">VC Dashboard<span>Venture Capital</span></div>
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
            <button class="tab-btn active" onclick="switchTab(this, 'kvca')">한국벤처캐피탈협회 <span class="tab-count">{len(kvca)}</span></button>
            <button class="tab-btn" onclick="switchTab(this, 'kgrowth')">한국성장금융 <span class="tab-count">{len(kgrowth)}</span></button>
            <button class="tab-btn" onclick="switchTab(this, 'kvic')">한국벤처투자 <span class="tab-count">{len(kvic)}</span></button>
        </div>

        <div class="search-bar">
            <input class="search-input" id="search-input" type="text"
                placeholder="공고명, LP명 키워드 검색..."
                oninput="doSearch()" onkeydown="if(event.key==='Escape')clearSearch()">
            <button class="search-btn" onclick="doSearch()">🔍 검색</button>
            <button class="search-clear" id="search-clear" onclick="clearSearch()">✕ 초기화</button>
            <label class="search-all-label">
                <input type="checkbox" id="search-all" onchange="doSearch()"> 전체 기관에서 검색
            </label>
        </div>
        <div class="search-result-count" id="search-result-count"></div>

        <div class="panel active" id="panel-kvca">
            <div class="panel-header">
                <span class="panel-title">한국벤처캐피탈협회 출자공고</span>
                <span style="display:flex;align-items:center;gap:16px;">
                    <span class="panel-count">총 {len(kvca)}건 · 최신순</span>
                    <a class="panel-link" href="https://www.kvca.or.kr/Program/invest/list.html?a_gb=board&a_cd=8&a_item=0&sm=2_2_2" target="_blank">원본 사이트 →</a>
                </span>
            </div>
            <div class="tbl-wrap"><table>
                <thead><tr><th>LP명</th><th>공고명</th><th style="width:100px">공고일</th><th style="width:100px">신청기한</th></tr></thead>
                <tbody>{kvca_rows(kvca)}</tbody>
            </table></div>
        </div>

        <div class="panel" id="panel-kgrowth">
            <div class="panel-header">
                <span class="panel-title">한국성장금융 출자사업공고</span>
                <span style="display:flex;align-items:center;gap:16px;">
                    <span class="panel-count">총 {len(kgrowth)}건 · 최신순</span>
                    <a class="panel-link" href="https://www.kgrowth.or.kr/notice.asp" target="_blank">원본 사이트 →</a>
                </span>
            </div>
            <div class="tbl-wrap"><table>
                <thead><tr><th style="width:50px">번호</th><th>공고명</th><th style="width:100px">작성일</th></tr></thead>
                <tbody>{kgrowth_rows(kgrowth)}</tbody>
            </table></div>
        </div>

        <div class="panel" id="panel-kvic">
            <div class="panel-header">
                <span class="panel-title">한국벤처투자 출자사업공지</span>
                <span style="display:flex;align-items:center;gap:16px;">
                    <span class="panel-count">총 {len(kvic)}건 · 최신순</span>
                    <a class="panel-link" href="https://www.kvic.or.kr/notice/kvic-notice/investment-business-notice" target="_blank">원본 사이트 →</a>
                </span>
            </div>
            <div class="tbl-wrap"><table>
                <thead><tr><th style="width:50px">번호</th><th style="width:90px">카테고리</th><th>제목</th><th style="width:100px">날짜</th></tr></thead>
                <tbody>{kvic_rows(kvic)}</tbody>
            </table></div>
        </div>

        <div class="update-info">마지막 업데이트: {now_str}</div>
    </main>
""" + JS_CODE + """
</body>
</html>"""
    return html

def main():
    print("크롤링 시작...")
    kvca = fetch_kvca()
    kvca.sort(key=lambda x: parse_date(x['date']), reverse=True)
    print(f"KVCA: {len(kvca)}건")

    kgrowth = fetch_kgrowth()
    kgrowth.sort(key=lambda x: parse_date(x['date']), reverse=True)
    print(f"한국성장금융: {len(kgrowth)}건")

    kvic = fetch_kvic()
    kvic.sort(key=lambda x: parse_date(x['date']), reverse=True)
    print(f"한국벤처투자: {len(kvic)}건")

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html = build_html(kvca, kgrowth, kvic, now_str)

    with open("investment.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("완료: investment.html 생성")

if __name__ == "__main__":
    main()
