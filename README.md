# 🤖 DevShot: AI 기술 블로그 요약 봇

매일 아침, 주요 기술 블로그(우아한형제들, 카카오, AWS 등)의 새 글을 크롤링하여 **Google Gemini AI**가 3줄 요약하고, **Discord**로 알림을 보내주는 자동화 봇입니다.

## 🛠 사용 기술
- **Language:** Python 3.10
- **AI Model:** Google Gemini 2.5 Flash
- **Infrastructure:** GitHub Actions (Crontab Schedule)
- **Notification:** Discord Webhook
- **Data:** RSS Feed Parsing

## ✨ 주요 기능
1. **자동 수집:** 매일 아침 8시(KST) 자동 실행
2. **AI 요약:** 긴 기술 블로그 글을 핵심만 3줄 요약 + 태그 추출
3. **중복 방지:** 이미 보낸 글은 `sent_logs.json`으로 관리하여 중복 전송 방지
4. **알림 전송:** 디스코드 임베드(Embed)를 활용한 깔끔한 카드 뉴스 형태 전송

## 🚀 봇 가져가서 쓰는 법 (How to use)
1. 이 저장소를 **Fork** 하세요 (우측 상단 버튼).
2. [Settings] -> [Secrets and variables] -> [Actions]에 가서 아래 2개를 등록하세요.
   - `GEMINI_API_KEY`: 구글 AI 키
   - `DISCORD_WEBHOOK_URL`: 본인 디스코드 웹훅 주소
3. [Actions] 탭에서 `Enable workflow` 버튼을 누르면 끝! 매일 아침 배달됩니다.
