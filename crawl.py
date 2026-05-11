import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse

def fetch_google_news():
    # 1. 설정: 검색 키워드
    query = "반도체 스마트팜 벤처투자" 
    encoded_query = urllib.parse.quote(query)
    
    # 구글 뉴스 RSS URL (검색어 포함)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'xml')
    items = soup.find_all('item')
    
    # 2. HTML 생성 시작
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html_template = f"""
    <!DOCTYPE html>
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
                <span>업데이트: {now}</span>
                <span class="count-badge" id="news-count">계산 중...</span>
            </div>
            <ul id="news-list">
    """
    
    # 3. 중복 제거 로직 및 뉴스 추출
    seen_titles = set()
    count = 0
    
    for item in items:
        title = item.title.text.strip()
        # 제목에서 언론사 이름이 붙어 나오는 경우(예: "... - 전자신문") 중복 방지를 위해 앞부분만 체크
        # 구글 뉴스는 보통 '제목 - 언론사' 형식이므로 '-' 기준으로 앞만 잘라 중복 체크를 정교화할 수 있습니다.
        main_title = title.split(' - ')[0] 
        
        if main_title not in seen_titles:
            seen_titles.add(main_title)
            link = item.link.text
            pub_date = item.pubDate.text[:16]
            source = item.source.text if item.source else "출처 미상"
            
            html_template += f"""
                <li>
                    <a href='{link}' target='_blank'>{title}</a>
                    <span class="meta">{source} | {pub_date}</span>
                </li>
            """
            count += 1
            
            # 1,000개가 넘어가면 중단
            if count >= 1000:
                break
    
    html_template = html_template.replace("계산 중...", f"검색된 뉴스: {count}건")
    html_template += """
            </ul>
        </div>
    </body>
    </html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    fetch_google_news()
