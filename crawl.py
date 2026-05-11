import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse

def fetch_google_news():
    # 1. 설정: 검색하고 싶은 키워드를 넣으세요 (한글 가능)
    query = "반도체 스마트팜" 
    encoded_query = urllib.parse.quote(query)
    
    # 구글 뉴스 RSS URL (검색어 포함)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    
    # XML 형태이므로 'xml' 파서 사용 (또는 기본 html.parser 사용 가능)
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
        <title>Google News Dashboard</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; padding: 30px; background-color: #f8f9fa; color: #333; }}
            .container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
            .date {{ color: #666; font-size: 0.9em; margin-bottom: 20px; }}
            ul {{ list-style: none; padding: 0; }}
            li {{ margin-bottom: 15px; padding: 10px; border-radius: 5px; transition: background 0.2s; }}
            li:hover {{ background-color: #f1f3f4; }}
            a {{ text-decoration: none; color: #1a0dab; font-weight: bold; font-size: 1.1em; }}
            .source {{ color: #006621; font-size: 0.85em; display: block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 "{query}" 관련 뉴스</h1>
            <p class="date">마지막 업데이트: {now}</p>
            <ul>
    """
    
    # 3. 뉴스 아이템 추출 (최신 15개)
    for item in items[:15]:
        title = item.title.text
        link = item.link.text
        pub_date = item.pubDate.text[:16] # 날짜 포맷 간단히
        source = item.source.text if item.source else "알 수 없음"
        
        html_template += f"""
            <li>
                <a href='{link}' target='_blank'>{title}</a>
                <span class="source">{source} | {pub_date}</span>
            </li>
        """
    
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
