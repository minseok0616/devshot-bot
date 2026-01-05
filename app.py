import os
import json
import requests
import feedparser
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ==========================================
# 1. 설정 및 환경변수 로드
# ==========================================
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# 필수 키 확인
if not API_KEY:
    print("❌ [오류] .env에서 GEMINI_API_KEY를 찾을 수 없습니다.")
    exit()
if not DISCORD_WEBHOOK_URL:
    print("⚠️ [주의] .env에서 DISCORD_WEBHOOK_URL을 찾을 수 없습니다. (디스코드 전송 불가)")

# Gemini 설정 (가성비 좋은 Flash 모델 사용)
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# 감시할 블로그 리스트
BLOG_FEEDS = {
    "우아한형제들": "https://techblog.woowahan.com/feed/",
    "카카오": "https://tech.kakao.com/feed/",
    "AWS 한국": "https://aws.amazon.com/ko/blogs/korea/feed/",
}

# 중복 방지를 위한 로그 파일명
LOG_FILE = "sent_logs.json"

# ==========================================
# 2. 헬퍼 함수들 (파일 입출력, AI, 디스코드)
# ==========================================

def load_sent_logs():
    """이미 보낸 글 목록(URL)을 파일에서 불러옵니다."""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return [] # 파일이 깨졌거나 비어있으면 빈 리스트 반환
    return []

def save_sent_logs(logs):
    """보낸 글 목록을 파일에 저장합니다."""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

def summarize_content(text):
    """AI에게 글 요약을 요청합니다."""
    prompt = f"""
    당신은 테크 뉴스레터 에디터입니다. 아래 기술 블로그 글을 읽고 개발자를 위해 요약해주세요.
    
    1. [한 줄 소개]: 이 글을 읽어야 하는 이유 (흥미 유발).
    2. [3줄 요약]: 핵심 기술 내용 3가지 (전문 용어 포함).
    3. [태그]: #키워드 3개.
    
    [본문 내용]:
    {text[:8000]}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"요약 실패: {e}"

# 블로그별 고유 색상 (Hex Code)
BLOG_COLORS = {
    "우아한형제들": 0x2AC1BC, # 민트색
    "카카오": 0xFEE500,      # 카카오 노랑
    "AWS 한국": 0xFF9900,    # AWS 주황
}

def send_to_discord(blog_name, title, link, summary):
    """디스코드 웹훅으로 메시지를 전송합니다."""
    embed_color = BLOG_COLORS.get(blog_name,0x00ff00)
    if not DISCORD_WEBHOOK_URL:
        return

    payload = {
        "username": "DevShot AI",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/2040/2040946.png",
        "embeds": [
            {
                "title": f"🔥 {title}",
                "url": link,
                "description": summary[:4000], # 디스코드 글자수 제한 대응
                "color": embed_color,
                "author": {"name": f"{blog_name}"},
                "footer": {"text": "DevShot News - 중복 방지 적용됨"},
                "timestamp": datetime.now().isoformat()
            }
        ]
    }
    
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL, 
            json=payload, 
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 204:
            print(f"✅ 디스코드 전송 완료: {title}")
        else:
            print(f"❌ 디스코드 전송 실패 (Code {response.status_code}): {response.text}")
    except Exception as e:
        print(f"❗ 네트워크 에러: {e}")

# ==========================================
# 3. 메인 로직
# ==========================================

def check_new_posts():
    print(f"🕵️  블로그 수색 시작 (최근 7일 & 중복 제거)\n")
    
    # 1. 날짜 기준 설정 (30일 전)
    search_start_date = datetime.now() - timedelta(days=30)
    
    # 2. 장부(로그) 불러오기
    sent_logs = load_sent_logs()
    original_log_count = len(sent_logs)
    new_sent_count = 0

    for blog_name, rss_url in BLOG_FEEDS.items():
        print(f"📡 [{blog_name}] 확인 중...")
        try:
            feed = feedparser.parse(rss_url)
            
            for entry in feed.entries:
                # 날짜 파싱
                if hasattr(entry, 'published_parsed'):
                    published_time = datetime(*entry.published_parsed[:6])
                else:
                    continue # 날짜 없으면 패스
                
                # [조건 1] 기간 체크 (최근 7일 이내인가?)
                if published_time > search_start_date:
                    
                    # [조건 2] 중복 체크 (이미 보낸 적 있는가?)
                    if entry.link in sent_logs:
                        # print(f"  └ 패스: 이미 보냄 ({entry.title})") # 너무 시끄러우면 주석 처리
                        continue

                    # ★ 신규 글 발견!
                    print(f"\n🚨 [NEW] {entry.title}")
                    
                    # 본문 추출
                    raw_content = ""
                    if hasattr(entry, 'content'):
                        raw_content = entry.content[0].value
                    elif hasattr(entry, 'summary'):
                        raw_content = entry.summary
                    
                    clean_text = BeautifulSoup(raw_content, "html.parser").get_text()

                    # AI 요약 및 전송
                    print("  └ 🤖 AI 요약 중...")
                    summary = summarize_content(clean_text)
                    
                    send_to_discord(blog_name, entry.title, entry.link, summary)
                    
                    # ★ 장부에 기록 (전송 성공 여부와 관계없이 시도했으면 기록)
                    sent_logs.append(entry.link)
                    new_sent_count += 1

                    print("  ☕ 5초 휴식...")  # <--- 추가
                    time.sleep(5)
                    
        except Exception as e:
            print(f"⚠️ [{blog_name}] 에러 발생: {e}")
            continue

    # 3. 변경된 장부 저장 (새로 보낸 게 있을 때만)
    if new_sent_count > 0:
        save_sent_logs(sent_logs)
        print(f"\n💾 장부 업데이트 완료! (총 {len(sent_logs)}개 기록됨)")
    else:
        print("\n😴 새로 보낸 글이 없습니다. (모두 이미 보냈거나 기간 지남)")

if __name__ == "__main__":
    check_new_posts()