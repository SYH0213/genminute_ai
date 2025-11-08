# GCP 배포 가이드 - AI 회의록 시스템

> **목적**: ngrok 대신 Google Cloud Platform(GCP)에 시스템을 배포하여 안정적이고 공개적인 서비스 운영

---

## 📋 목차

1. [배포 방법 비교](#배포-방법-비교)
2. [Compute Engine 배포 (추천)](#compute-engine-배포-단계별-가이드)
3. [HTTPS 설정 (선택사항)](#https-설정-도메인-있으면)
4. [데이터 백업](#데이터-백업-권장사항)
5. [비용 예상](#비용-예상)
6. [ngrok vs GCP 비교](#ngrok-vs-gcp-비교)

---

## 배포 방법 비교

현재 시스템에 적합한 3가지 옵션:

### 1. **Compute Engine (VM)** ⭐ 추천 (초보자용)

- **장점**:
  - 기존 코드 거의 그대로 사용
  - 설정 간단
  - SQLite/ChromaDB 그대로 사용 가능
- **단점**:
  - 서버 관리 필요
  - 항상 실행 시 비용 발생
- **비용**: ~$5-20/월 (항상 켜두면)

### 2. **Cloud Run** (Docker 경험 있으면)

- **장점**:
  - 자동 스케일링
  - 사용한 만큼만 과금
  - 관리 편함
- **단점**:
  - SQLite/ChromaDB를 Cloud SQL/Cloud Storage로 마이그레이션 필요
- **비용**: ~$0-10/월 (사용량 기준)

### 3. **App Engine**

- **장점**:
  - 완전 관리형
  - 배포 간단
- **단점**:
  - SQLite 사용 불가
  - 파일 저장 제한
- **비용**: ~$10-30/월

---

## 🚀 Compute Engine 배포 (단계별 가이드)

### 1단계: GCP 프로젝트 설정

1. [GCP Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성: `minute-ai-project`
3. 결제 계정 연결 ($300 무료 크레딧 사용 가능)
4. Compute Engine API 활성화

### 2단계: VM 인스턴스 생성

**GCP Console에서 설정:**

1. **Compute Engine** → **VM 인스턴스** → **인스턴스 만들기**
2. **설정값**:
   - **이름**: `minute-ai-server`
   - **리전**: `asia-northeast3` (서울)
   - **머신 유형**: `e2-medium` (2vCPU, 4GB RAM) - 시작용
   - **부팅 디스크**: Ubuntu 22.04 LTS, 30GB
   - **방화벽**: HTTP, HTTPS 트래픽 허용 ✅ 체크
3. **만들기** 클릭

### 3단계: 방화벽 규칙 추가 (Flask 포트 열기)

**GCP Console에서:**

```
VPC 네트워크 → 방화벽 → 방화벽 규칙 만들기

설정:
- 이름: allow-flask
- 대상: 네트워크의 모든 인스턴스
- 소스 IP 범위: 0.0.0.0/0
- 프로토콜 및 포트: tcp:5050 (또는 사용할 포트)
```

### 4단계: VM에 SSH 접속 및 환경 설정

**VM 인스턴스 페이지에서 SSH 버튼 클릭 후:**

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. Python 3.11 설치
sudo apt install -y python3.11 python3.11-venv python3-pip

# 3. Git 설치 (코드 가져오기용)
sudo apt install -y git

# 4. FFmpeg 설치 (오디오 처리용)
sudo apt install -y ffmpeg

# 5. 프로젝트 디렉토리 생성
mkdir -p /home/$USER/minute_ai
cd /home/$USER/minute_ai
```

### 5단계: 코드 업로드

#### 방법 1: GitHub 사용 (추천)

**로컬에서 먼저 GitHub에 푸시:**

```bash
cd /mnt/c/Users/SBA/Project/minute_ai

# Git 초기화 (이미 했으면 skip)
git init
git add .
git commit -m "Initial commit for GCP deployment"
git branch -M main

# GitHub에 푸시
git remote add origin https://github.com/your-username/minute-ai.git
git push -u origin main
```

**VM에서 클론:**

```bash
cd /home/$USER/minute_ai
git clone https://github.com/your-username/minute-ai.git .
```

#### 방법 2: SCP로 직접 업로드

**로컬 터미널에서 (WSL):**

```bash
gcloud compute scp --recurse /mnt/c/Users/SBA/Project/minute_ai/* minute-ai-server:~/minute_ai/
```

#### 방법 3: GCP Console에서 파일 업로드

- SSH 창 상단의 톱니바퀴 → **파일 업로드**

### 6단계: Python 환경 설정

```bash
cd /home/$USER/minute_ai

# 가상환경 생성
python3.11 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt
```

### 7단계: 환경 변수 설정

```bash
# .env 파일 생성
nano .env
```

**.env 파일 내용 (기존 로컬 .env 복사):**

```bash
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
SECRET_KEY=your_secret_key
GEMINI_API_KEY=your_gemini_key

# 기타 필요한 환경 변수들...
```

**저장**: `Ctrl + X` → `Y` → `Enter`

#### ⚠️ 중요: Google OAuth 리디렉션 URI 업데이트

```
Google Cloud Console → API 및 서비스 → 사용자 인증 정보
→ OAuth 2.0 클라이언트 ID 수정

승인된 리디렉션 URI에 추가:
- http://[VM의_외부_IP]:5050/callback
- http://[도메인]:5050/callback  (도메인 있으면)
```

### 8단계: ngrok 제거 및 앱 수정

```bash
# app.py 수정
nano app.py
```

**수정 내용:**

```python
# ngrok 관련 코드 제거 또는 주석 처리
# from pyngrok import ngrok  <- 삭제
# ngrok.connect() 관련 코드 <- 삭제

# Flask 실행 부분 수정
if __name__ == '__main__':
    # 모든 IP에서 접속 허용 (0.0.0.0으로 변경)
    app.run(host='0.0.0.0', port=5050, debug=False)
```

### 9단계: 서비스 자동 시작 설정 (systemd)

**서비스 파일 생성:**

```bash
sudo nano /etc/systemd/system/minute-ai.service
```

**파일 내용:**

```ini
[Unit]
Description=Minute AI Flask Application
After=network.target

[Service]
User=your_username
WorkingDirectory=/home/your_username/minute_ai
Environment="PATH=/home/your_username/minute_ai/venv/bin"
ExecStart=/home/your_username/minute_ai/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

⚠️ **주의**: `your_username`을 실제 사용자명으로 변경 (`echo $USER`로 확인)

**서비스 활성화 및 시작:**

```bash
# 서비스 재로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable minute-ai

# 서비스 시작
sudo systemctl start minute-ai

# 상태 확인
sudo systemctl status minute-ai

# 로그 실시간 확인
sudo journalctl -u minute-ai -f
```

**유용한 명령어:**

```bash
# 서비스 중지
sudo systemctl stop minute-ai

# 서비스 재시작
sudo systemctl restart minute-ai

# 로그 확인 (마지막 100줄)
sudo journalctl -u minute-ai -n 100
```

### 10단계: 접속 확인

```bash
# VM의 외부 IP 확인
gcloud compute instances list

# 또는 GCP Console에서 확인
# Compute Engine → VM 인스턴스 → 외부 IP 복사
```

**브라우저에서 접속:**

```
http://[외부_IP]:5050
```

예: `http://34.64.123.45:5050`

---

## 🔒 HTTPS 설정 (도메인 있으면)

### 1. 도메인 연결

**Cloud DNS 또는 외부 도메인 관리자에서:**

```
A 레코드 추가:
minute-ai.yourdomain.com → [VM 외부 IP]
```

### 2. Nginx 리버스 프록시 + Let's Encrypt SSL

**Nginx 및 Certbot 설치:**

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

**Nginx 설정 파일 생성:**

```bash
sudo nano /etc/nginx/sites-available/minute-ai
```

**파일 내용:**

```nginx
server {
    listen 80;
    server_name minute-ai.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**설정 활성화:**

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/minute-ai /etc/nginx/sites-enabled/

# 설정 파일 문법 검사
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

**SSL 인증서 발급 (무료):**

```bash
sudo certbot --nginx -d minute-ai.yourdomain.com
```

**자동 갱신 확인:**

```bash
# Certbot은 자동으로 갱신 설정됨
sudo systemctl status certbot.timer

# 수동 갱신 테스트
sudo certbot renew --dry-run
```

**Google OAuth URI 업데이트:**

```
https://minute-ai.yourdomain.com/callback 추가
```

---

## 📊 데이터 백업 권장사항

### 자동 백업 스크립트 설정

```bash
# 백업 디렉토리 생성
mkdir -p /home/$USER/backups

# Cron 작업 설정
crontab -e
```

**Crontab에 추가:**

```bash
# 매일 새벽 3시에 백업
0 3 * * * tar -czf /home/$USER/backups/minute_ai_$(date +\%Y\%m\%d).tar.gz /home/$USER/minute_ai/instance /home/$USER/minute_ai/uploads /home/$USER/minute_ai/chroma_db

# 30일 이상 된 백업 파일 삭제
0 4 * * * find /home/$USER/backups -name "minute_ai_*.tar.gz" -mtime +30 -delete
```

### Cloud Storage 백업 (선택사항)

```bash
# gsutil 설치 (이미 설치되어 있음)
# GCS 버킷 생성
gsutil mb -l asia-northeast3 gs://minute-ai-backups

# 백업 업로드 스크립트
0 5 * * * gsutil cp /home/$USER/backups/minute_ai_$(date +\%Y\%m\%d).tar.gz gs://minute-ai-backups/
```

---

## 💰 비용 예상

### Compute Engine (e2-medium, 서울 리전)

| 항목 | 비용 |
|------|------|
| VM 인스턴스 (e2-medium) | ~$25/월 |
| 스토리지 (30GB SSD) | ~$2/월 |
| 네트워크 아웃바운드 | ~$1-5/월 |
| **총 예상 비용** | **~$30-35/월** |

### 비용 절감 팁

1. **자동 종료 스크립트**
   ```bash
   # 밤 11시에 자동 종료
   0 23 * * * sudo shutdown -h now

   # 아침 8시에 자동 시작 (GCP Cloud Scheduler 사용)
   ```

2. **Preemptible VM 사용**
   - 80% 할인 (~$6/월)
   - 단점: 24시간마다 자동 종료됨
   - 재시작 스크립트 필요

3. **스냅샷 대신 gsutil 백업**
   - 스냅샷: $0.026/GB/월
   - Cloud Storage: $0.020/GB/월

4. **무료 티어 활용**
   - 매월 1GB 네트워크 아웃바운드 무료
   - 30GB-월 표준 스토리지 무료

---

## ✅ ngrok vs GCP 비교

| 항목 | ngrok (현재) | GCP Compute Engine |
|------|-------------|-------------------|
| **URL** | 임시 (재시작 시 변경) | 고정 IP/도메인 |
| **안정성** | 세션 끊김 가능 | 24/7 안정 운영 |
| **속도** | 터널링으로 느림 | 직접 연결, 빠름 |
| **비용** | 무료 (제한적) | ~$30/월 |
| **SSL** | ngrok 자동 제공 | Let's Encrypt 무료 |
| **접속 제한** | 연결 수 제한 | 무제한 |
| **커스텀 도메인** | 유료 ($8/월~) | 무료 |
| **서비스 신뢰도** | 개발/테스트용 | 프로덕션 가능 |

### GCP 배포 시 ngrok 제거 사항

```python
# app.py에서 삭제할 코드들:

# 1. import 제거
from pyngrok import ngrok  # ← 삭제

# 2. ngrok 터널링 코드 제거
public_url = ngrok.connect(5050)  # ← 삭제
print(f"Public URL: {public_url}")  # ← 삭제

# 3. Flask 실행 설정 변경
# 변경 전:
app.run(host='127.0.0.1', port=5050, debug=True)

# 변경 후:
app.run(host='0.0.0.0', port=5050, debug=False)
```

---

## 🔧 문제 해결

### 1. 서비스가 시작되지 않을 때

```bash
# 로그 확인
sudo journalctl -u minute-ai -n 50 --no-pager

# Python 경로 확인
which python
# /home/username/minute_ai/venv/bin/python

# 수동 실행 테스트
cd /home/$USER/minute_ai
source venv/bin/activate
python app.py
```

### 2. 포트 접속이 안 될 때

```bash
# 방화벽 규칙 확인
gcloud compute firewall-rules list | grep 5050

# Flask가 실제로 실행 중인지 확인
sudo netstat -tulpn | grep 5050

# VM 외부 IP 확인
curl ifconfig.me
```

### 3. 메모리 부족 시

```bash
# 메모리 사용량 확인
free -h

# 스왑 메모리 추가 (4GB)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구 설정
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 4. 디스크 용량 부족 시

```bash
# 디스크 사용량 확인
df -h

# 큰 파일 찾기
du -ah /home/$USER/minute_ai | sort -rh | head -20

# 로그 파일 정리
sudo journalctl --vacuum-time=7d
```

---

## 📚 추가 참고 자료

- [GCP Compute Engine 문서](https://cloud.google.com/compute/docs)
- [Flask 프로덕션 배포 가이드](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Let's Encrypt 공식 문서](https://letsencrypt.org/getting-started/)
- [systemd 서비스 관리](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

## 🎯 체크리스트

배포 완료 확인:

- [ ] VM 인스턴스 생성 완료
- [ ] 방화벽 규칙 설정 완료
- [ ] 코드 업로드 완료
- [ ] Python 환경 설정 완료
- [ ] .env 파일 설정 완료
- [ ] Google OAuth URI 업데이트 완료
- [ ] systemd 서비스 등록 완료
- [ ] 외부 IP로 접속 확인
- [ ] 자동 백업 설정 (선택)
- [ ] HTTPS 설정 (선택)

---

**작성일**: 2025-11-08
**버전**: 1.0
**대상**: AI 회의록 시스템 GCP 배포
