# 📞 AI 에이전트로 전화 설문조사 자동화하기

LiveKit + Twilio + OpenAI Realtime API를 활용한 전화 설문조사 자동화 Agent입니다.

사람 상담원 없이 수백 명에게 실시간으로 설문을 진행하고, 비용은 80% 이상 절감할 수 있습니다.

## 🛠 사용 기술

| **기술**                      | **역할**                                     |
| --------------------------- | ------------------------------------------ |
| LiveKit Agents SDK          | 음성 Agent 플랫폼, SIP 연결, Room 관리, 음성 파이프라인 통합 |
| Twilio Elastic SIP Trunking | 실제 전화 발신 (SIP 트렁킹)                         |
| OpenAI Realtime API         | 실시간 대화 처리 및 답변 인식                          |


## 작업 프로세스
```
[CSV에서 데이터 읽기]
    ↓
[MakeSurveyCall 실행]
    ↓
[LiveKit Agent Dispatch + Twilio SIP 발신]
    ↓
[SurveyAgent가 수신자와 통화 (실시간 음성 통화)]
    ↓
[응답 기록 (CSV 업데이트)]
```

## ⚡ 설치 방법 (Setup)

### 1. 코드 내려받기

먼저 프로젝트를 클론합니다:

```bash
gh repo clone Marker-Inc-Korea/phone-survey-agent
cd phone-survey-agent
```

### 2. 의존성 설치

`uv`를 이용해 필요한 파이썬 패키지를 한 번에 설치합니다.

```bash
uv sync
```

### 3. 환경변수 설정

`.env.example` 파일을 복사해 `.env`를 만들고, 다음을 채워주세요.
```
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=your_livekit_server_url
OPENAI_API_KEY=your_openai_api_key
SIP_OUTBOUND_TRUNK_ID=your_sip_trunk_id  # 5단계 완료 후 입력
```

### 4. 모델 파일 다운로드

VAD·노이즈 캔슬링 기능을 쓰려면 모델 파일을 먼저 받아야 합니다.

```bash
uv run survey_calling_agent.py download-files
```
- Silero VAD (발화 탐지)
- Noise Cancellation (소음 제거)


### 5. SIP 트렁크 연결

전화 발신을 위해 SIP 트렁크를 설정해야 합니다.

1. **Twilio SIP 트렁크 생성 및 설정**
    
    Twilio에서 SIP 트렁크를 생성하고 설정합니다.
    
    👉 [Twilio SIP 트렁크 설정 가이드](https://docs.livekit.io/sip/quickstarts/configuring-twilio-trunk/)
    
2. **LiveKit 서버에 SIP 트렁크 연결**
    
    Twilio 트렁크를 LiveKit 서버에 연결합니다.
    
    👉 [LiveKit SIP 트렁크 설정 가이드](https://docs.livekit.io/sip/quickstarts/configuring-sip-trunk/#livekit-setup)
    
3. **.env 파일 업데이트**
    
    발급된 **Outbound Trunk SID**를 `.env` 파일의 `SIP_OUTBOUND_TRUNK_ID`에 입력합니다.

## 🚀 Agent 실행하기

### 1. Agent 실행
```bash
uv run survey_calling_agent.py dev
```
- LiveKit 서버에 연결해 발신 요청 대기

### 2. 설문 전화 걸기
```bash
uv run make_survey_call.py
```
- survey_data.csv를 읽어 설문 대상자에게 자동 발신
- 응답을 듣고 CSV 파일에 결과 자동 기록


## 📝 CSV 포맷

| **전화번호 (Phone Number)** | **질문 (Question)**        | **답변 (Answer)** | **상태 (Status)** |
| ----------------------- | ------------------------ | --------------- | --------------- |
| +821012345678           | 이재명과 홍준표 중 누구를 더 선호하시나요? |                 |                 |


- Phone Number: 국제전화번호 형식 (+82...)
- Question: 설문 질문
- Answer: 통화 후 자동 기록
- Status: 완료 시 Completed 자동 기록

⚠️ CSV 파일은 UTF-8 인코딩 필수, 초기에는 Answer/Status를 비워두세요.

## 🏷️ License

MIT © Marker-Inc-Korea
