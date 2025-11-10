# GCP 배포 가이드 - AI 회의록 시스템 (Minute AI)

> **목적**: Google Cloud Platform(GCP)에 시스템을 배포하여 안정적이고 공개적인 서비스 운영
>
> **버전**: 2.1 (2025-11-10 업데이트)
>
> **주요 변경사항**: Gunicorn + Nginx 프로덕션 배포, 보안 강화, Firebase 제약사항 명시

---

## 📋 목차

1. [배포 방법 비교](#배포-방법-비교)
2. [Compute Engine 배포 (추천)](#compute-engine-배포-단계별-가이드)
3. [HTTPS 설정 (선택사항)](#https-설정-도메인-있으면)
4. [데이터 백업](#데이터-백업-권장사항)
5. [비용 예상](#비용-예상)
6. [문제 해결](#문제-해결)

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
  - ⚠️ **SQLite는 에페메럴 스토리지라 사용 불가** (재시작 시 데이터 손실)
  - **Cloud SQL(PostgreSQL/MySQL) + Cloud Storage 마이그레이션 필수**
  - ChromaDB도 영구 저장소로 이관 필요
  - 코드 수정 범위가 큼 (DB 연결, 파일 저장 로직)
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

   **기본 정보:**
   - **이름**: `minute-ai-server`
   - **리전**: `asia-northeast3` (서울)
   - **영역**: `asia-northeast3-a` (자동 선택)

   **머신 구성:**
   - **시리즈**: **E2** ⚠️ 중요: ARM 아키텍처(T2A)는 선택하지 마세요!
   - **머신 유형**: `e2-medium` (2vCPU, 4GB RAM)
     - 비용: ~$30-40/월
     - 트래픽 증가 시 `e2-standard-2` 권장

   **부팅 디스크:**
   - **운영체제**: Ubuntu
   - **버전**: Ubuntu 22.04 LTS (x86/64)
   - **부팅 디스크 유형**: 균형적 영구 디스크 (표준 영구 디스크도 OK)
   - **크기**: 30GB (최소값, 필요 시 50GB)
   - **삭제 규칙**: ✅ **인스턴스를 삭제할 때 부팅 디스크 유지** (권장)
     - 데이터 보존 및 복구 가능
     - 비용: 디스크 삭제 시 ~$2-4/월 절약
     - 백업이 있다면 "삭제"해도 OK

   **방화벽:**
   - ✅ **HTTP 트래픽 허용**
   - ✅ **HTTPS 트래픽 허용**

3. **만들기** 클릭

**⚠️ 아키텍처 호환성 주의:**
```
"부팅 디스크의 아키텍처가 x86/64 아키텍처여야 합니다" 메시지가 나온다면:
→ 머신 시리즈를 T2A에서 E2로 변경하세요!

❌ 피해야 할: t2a-standard-1 (ARM 아키텍처, Ubuntu 22.04 비호환)
✅ 사용 가능: e2-medium, e2-small, n1-standard-1 (x86/64)
```

### 3단계: 방화벽 규칙 추가

**GCP Console에서:**

```
VPC 네트워크 → 방화벽 → 방화벽 규칙 만들기

설정 1 (HTTP/HTTPS만 공개 - 권장):
- 이름: allow-http-https
- 대상: 네트워크의 모든 인스턴스
- 소스 IP 범위: 0.0.0.0/0
- 프로토콜 및 포트: tcp:80,tcp:443

⚠️ Flask 포트(5050)는 내부만 접근 가능하도록 설정 (Nginx로 리버스 프록시)
```

**⚠️ 보안 주의사항**:
- **Flask 포트(5050)를 전 세계에 공개하지 마세요!**
- 프로덕션에서는 Nginx가 80/443을 받아서 내부 5050으로 전달
- 5050은 `127.0.0.1`(localhost)에만 바인딩

### 4단계: VM에 SSH 접속 및 환경 설정

**VM 인스턴스 페이지에서 SSH 버튼 클릭 후:**

```bash
# 1. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 2. 기본 패키지 설치
sudo apt install -y \
    git \
    ffmpeg \
    graphviz \
    build-essential \
    software-properties-common

# 3. Python 3.11 설치 (Deadsnakes PPA 사용)
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev

# Python 3.11을 기본 python3로 설정 (선택사항)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# 4. Miniconda 설치 (Conda 사용 시 - 추천)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
~/miniconda3/bin/conda init bash
source ~/.bashrc

# 5. 프로젝트 디렉토리 생성
mkdir -p /home/$USER/minute_ai
cd /home/$USER/minute_ai
```

**설치된 패키지 확인:**

```bash
python3 --version  # Python 3.11.x 확인
git --version
ffmpeg -version
dot -V  # Graphviz 확인 (마인드맵 기능용)
```

**⚠️ 중요**: Ubuntu 22.04에서 `python3.11`은 Deadsnakes PPA가 필요합니다. Conda를 사용하면 PPA 없이도 Python 3.11.13을 정확히 설치할 수 있습니다.

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

#### 방법 A: Conda 사용 (추천 - 재현성 보장)

```bash
cd /home/$USER/minute_ai

# Conda 환경 생성 (Python 3.11.13 고정)
conda env create -f environment_crossplatform.yml

# 환경 활성화
conda activate genminute

# 설치 확인
python --version  # Python 3.11.13 확인
pip list | grep langchain  # LangChain 1.0.5 확인
```

**Conda 환경의 장점:**
- Python 3.11.13으로 정확히 고정 (팀 협업/배포 일관성)
- LangChain 1.0.x 패밀리 자동 설치
- 크로스 플랫폼 호환성 보장

#### 방법 B: pip 사용

```bash
cd /home/$USER/minute_ai

# 가상환경 생성
python3.11 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip

# 의존성 설치 (크로스 플랫폼 버전)
pip install -r requirements_crossplatform.txt

# 설치 확인
python --version
pip list | grep langchain
```

**⚠️ 중요**: `requirements.txt` 대신 `requirements_crossplatform.txt`를 사용하세요!
- LangChain 1.0.5로 업그레이드됨
- 플랫폼별 빌드 해시 제거 (Linux/Mac/Windows 모두 지원)
- pydot, graphviz 포함 (마인드맵 기능)

### 7단계: 환경 변수 설정

```bash
# .env 파일 생성 (템플릿 복사)
cp .env.example .env

# .env 파일 편집
nano .env
```

**.env 파일 필수 설정 항목:**

```bash
# Google/OpenAI API Keys (필수)
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_key

# Firebase Configuration (필수 - Client-side)
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_MEASUREMENT_ID=your_measurement_id

# Flask Configuration (필수)
FLASK_SECRET_KEY=generate_with_secrets_token_hex_32
ADMIN_EMAILS=admin@example.com,admin2@example.com

# Google Cloud Storage (선택)
GCS_BUCKET_NAME=your_bucket_name

# LangSmith Tracing (선택)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=minute-ai-production
```

**Flask Secret Key 생성:**

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# 출력된 키를 FLASK_SECRET_KEY에 복사
```

**저장**: `Ctrl + X` → `Y` → `Enter`

#### ⚠️ 중요: Firebase 콘솔 설정

**Firebase Console (https://console.firebase.google.com/):**

1. **Authentication** → **Sign-in method**
   - Google 로그인 활성화
   - **승인된 도메인**:
     - ⚠️ **IP 주소는 불가능합니다!** 도메인만 허용됨
     - 도메인이 있는 경우: `yourdomain.com` 추가
     - 도메인이 없는 경우: **HTTPS 설정 필수** (Let's Encrypt) 또는 테스트 목적으로 `localhost` 사용

2. **프로젝트 설정** → **일반**
   - 웹 앱 등록 후 구성 값 복사 → .env에 입력
   - Storage 버킷: `your_project_id.appspot.com` 형식 확인

**⚠️ Firebase 제약사항**:
- IP 주소로는 Firebase 인증이 작동하지 않습니다
- **프로덕션 배포 시 도메인 + HTTPS가 필수**입니다
- 테스트 목적이라면 SSH 포트 포워딩을 고려하세요:
  ```bash
  # 로컬에서 실행
  gcloud compute ssh minute-ai-server -- -L 5050:localhost:5050
  # 이후 http://localhost:5050 접속
  ```

### 8단계: 데이터베이스 초기화 (중요!)

**⚠️ 필수 단계**: 앱 실행 전 데이터베이스 스키마 생성이 필요합니다.

```bash
cd /home/$USER/minute_ai

# Conda 사용 시
conda activate genminute

# pip 사용 시
source venv/bin/activate

# 데이터베이스 초기화 (처음 한 번만)
python init_db.py
```

**생성되는 테이블:**
- `meeting_dialogues` - 음성인식 결과
- `meeting_minutes` - 회의록
- `meeting_mindmap` - 마인드맵
- `users` - 사용자 정보
- `meeting_shares` - 공유 정보

**초기화 확인:**

```bash
ls -lh database/minute_ai.db  # DB 파일 생성 확인
sqlite3 database/minute_ai.db "SELECT name FROM sqlite_master WHERE type='table';"
# 5개 테이블이 출력되어야 함
```

### 9단계: Gunicorn 설치 (프로덕션 서버)

**⚠️ 중요**: Flask 내장 서버는 개발용입니다. 프로덕션에서는 **Gunicorn**을 사용하세요.

```bash
# Conda 환경에서
conda activate genminute
pip install gunicorn

# pip venv 환경에서
source venv/bin/activate
pip install gunicorn

# 설치 확인
gunicorn --version
```

**Gunicorn 테스트 실행:**

```bash
cd /home/$USER/minute_ai

# 4 워커로 실행 (CPU 코어 수에 따라 조정)
gunicorn --bind 127.0.0.1:5050 --workers 4 app:app

# 정상 작동 확인 후 Ctrl+C로 종료
```

**⚠️ 주의**:
- `127.0.0.1`로 바인딩 (외부 직접 접근 차단)
- Nginx가 리버스 프록시로 80/443 → 5050 전달
- `--workers` 수: `(2 × CPU 코어 수) + 1` 권장

### 10단계: 서비스 자동 시작 설정 (systemd)

**서비스 파일 생성:**

```bash
sudo nano /etc/systemd/system/minute-ai.service
```

#### 옵션 A: Conda 환경 사용 시 (Gunicorn)

```ini
[Unit]
Description=Minute AI Gunicorn Application
After=network.target

[Service]
Type=notify
User=your_username
Group=your_username
WorkingDirectory=/home/your_username/minute_ai
Environment="PATH=/home/your_username/miniconda3/envs/genminute/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/home/your_username/minute_ai/.env
ExecStart=/home/your_username/miniconda3/envs/genminute/bin/gunicorn \
    --bind 127.0.0.1:5050 \
    --workers 4 \
    --timeout 300 \
    --access-logfile /var/log/minute-ai/access.log \
    --error-logfile /var/log/minute-ai/error.log \
    app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 옵션 B: pip venv 사용 시 (Gunicorn)

```ini
[Unit]
Description=Minute AI Gunicorn Application
After=network.target

[Service]
Type=notify
User=your_username
Group=your_username
WorkingDirectory=/home/your_username/minute_ai
Environment="PATH=/home/your_username/minute_ai/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/home/your_username/minute_ai/.env
ExecStart=/home/your_username/minute_ai/venv/bin/gunicorn \
    --bind 127.0.0.1:5050 \
    --workers 4 \
    --timeout 300 \
    --access-logfile /var/log/minute-ai/access.log \
    --error-logfile /var/log/minute-ai/error.log \
    app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

⚠️ **주의**:
- `your_username`을 실제 사용자명으로 변경 (`echo $USER`로 확인)
- `EnvironmentFile`로 .env 파일 자동 로드
- 로그 디렉토리 생성 필요:
  ```bash
  sudo mkdir -p /var/log/minute-ai
  sudo chown $USER:$USER /var/log/minute-ai
  ```

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

### 11단계: Nginx 리버스 프록시 설정 (필수)

**⚠️ 중요**: Gunicorn은 127.0.0.1에만 바인딩되므로, Nginx로 외부 접근을 허용해야 합니다.

```bash
# Nginx 설치
sudo apt install -y nginx

# Nginx 설정 파일 생성
sudo nano /etc/nginx/sites-available/minute-ai
```

**설정 파일 내용:**

```nginx
server {
    listen 80;
    server_name _;  # 도메인이 있으면 yourdomain.com으로 변경

    client_max_body_size 500M;  # 대용량 파일 업로드 허용
    client_body_timeout 300s;
    proxy_read_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 지원 (업로드 진행 상황)
        proxy_buffering off;
        proxy_cache off;
    }
}
```

**Nginx 활성화:**

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/minute-ai /etc/nginx/sites-enabled/

# 기본 설정 비활성화 (선택)
sudo rm /etc/nginx/sites-enabled/default

# 설정 문법 검사
sudo nginx -t

# Nginx 시작 및 활성화
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### 12단계: 접속 확인

```bash
# VM의 외부 IP 확인
gcloud compute instances list

# 또는 GCP Console에서 확인
# Compute Engine → VM 인스턴스 → 외부 IP 복사
```

**브라우저에서 접속:**

```
http://[외부_IP]
```

예: `http://34.64.123.45`

**⚠️ Firebase 인증 문제**:
- IP 주소로는 Firebase 인증이 작동하지 않습니다
- **도메인 + HTTPS 설정이 필수**입니다 (다음 섹션 참조)
- 테스트 목적: SSH 포트 포워딩 사용

**로그 확인 (문제 발생 시):**

```bash
# Gunicorn 서비스 상태
sudo systemctl status minute-ai

# Gunicorn 로그
sudo journalctl -u minute-ai -n 100 --no-pager
tail -f /var/log/minute-ai/error.log

# Nginx 로그
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# 포트 리스닝 확인
sudo netstat -tulpn | grep -E '(80|5050)'
```

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
0 3 * * * tar -czf /home/$USER/backups/minute_ai_$(date +\%Y\%m\%d).tar.gz /home/$USER/minute_ai/database /home/$USER/minute_ai/uploads

# 30일 이상 된 백업 파일 삭제
0 4 * * * find /home/$USER/backups -name "minute_ai_*.tar.gz" -mtime +30 -delete
```

**백업 대상:**
- `database/` - SQLite DB (minute_ai.db) + ChromaDB (vector_db/)
- `uploads/` - 업로드된 오디오/비디오 파일

### Cloud Storage 백업 (선택사항)

**gsutil 설치 확인 및 설치:**

```bash
# gsutil 확인
which gsutil

# 없으면 google-cloud-sdk 설치
sudo apt install -y google-cloud-sdk

# 인증 (처음 한 번만)
gcloud auth login
```

**GCS 버킷 생성 및 백업:**

```bash
# GCS 버킷 생성
gsutil mb -l asia-northeast3 gs://minute-ai-backups-$(date +%Y%m)

# 백업 업로드 스크립트 (crontab에 추가)
0 5 * * * gsutil cp /home/$USER/backups/minute_ai_$(date +\%Y\%m\%d).tar.gz gs://minute-ai-backups-*/

# 90일 이상 된 GCS 백업 자동 삭제 (Lifecycle 설정)
gsutil lifecycle set /dev/stdin gs://minute-ai-backups-* <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF
```

---

## 💰 비용 예상

### Compute Engine (e2-medium, 서울 리전)

| 항목 | 비용 (추정치) |
|------|------|
| VM 인스턴스 (e2-medium) | ~$30-40/월 |
| 스토리지 (30GB SSD) | ~$2-4/월 |
| 네트워크 아웃바운드 | ~$1-10/월 |
| **총 예상 비용** | **~$35-55/월** |

**⚠️ 주의**: 실제 비용은 사용량(네트워크, 디스크 I/O, 지속 시간)에 따라 변동됩니다. [GCP 요금 계산기](https://cloud.google.com/products/calculator)로 정확한 예상 비용을 확인하세요.

### 비용 절감 팁

1. **Instance Schedules (VM 자동 시작/중지)**

   ⚠️ **주의**: 크론으로는 VM 자체를 켤 수 없습니다!

   **GCP Console에서 설정:**
   ```
   Compute Engine → Instance Schedules → 일정 만들기

   설정:
   - 시작 일정: 평일 오전 9시
   - 중지 일정: 평일 오후 6시
   - 시간대: Asia/Seoul
   - 대상 VM: minute-ai-server
   ```

   **또는 gcloud 명령어:**
   ```bash
   # 일정 생성
   gcloud compute resource-policies create instance-schedule minute-ai-schedule \
       --region=asia-northeast3 \
       --vm-start-schedule='0 9 * * 1-5' \
       --vm-stop-schedule='0 18 * * 1-5' \
       --timezone='Asia/Seoul'

   # VM에 일정 적용
   gcloud compute instances add-resource-policies minute-ai-server \
       --resource-policies=minute-ai-schedule \
       --zone=asia-northeast3-a
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

### 5. LangChain ImportError 발생 시

```bash
# 증상: ModuleNotFoundError: No module named 'langchain_classic'

# 원인: requirements_crossplatform.txt가 아닌 구버전 requirements.txt 사용

# 해결:
pip uninstall langchain langchain-core langchain-chroma -y
pip install -r requirements_crossplatform.txt

# 버전 확인
pip list | grep langchain
# langchain==1.0.5
# langchain-core==1.0.4
# langchain-classic==1.0.0
```

### 6. 마인드맵 생성 실패 시

```bash
# 증상: pydot.InvocationException 또는 graphviz 관련 오류

# 원인: graphviz 시스템 패키지 미설치

# 해결:
sudo apt install -y graphviz
dot -V  # 설치 확인

# 서비스 재시작
sudo systemctl restart minute-ai
```

### 7. Firebase 인증 실패 시

**증상**: "Firebase API key not found" 또는 로그인 불가

**해결**:

1. `.env` 파일 확인:
   ```bash
   cat .env | grep FIREBASE
   # FIREBASE_API_KEY, FIREBASE_AUTH_DOMAIN 등 13개 항목 확인
   ```

2. Firebase Console 설정 확인:
   - Authentication → Sign-in method → Google 활성화
   - 승인된 도메인에 VM IP 추가

3. 서비스 재시작:
   ```bash
   sudo systemctl restart minute-ai
   ```

---

## 📚 추가 참고 자료

- [GCP Compute Engine 문서](https://cloud.google.com/compute/docs)
- [Flask 프로덕션 배포 가이드](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Let's Encrypt 공식 문서](https://letsencrypt.org/getting-started/)
- [systemd 서비스 관리](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

## 🎯 배포 완료 체크리스트

### 필수 단계

- [ ] **1단계**: GCP 프로젝트 생성 및 결제 설정
- [ ] **2단계**: VM 인스턴스 생성 (e2-medium, Ubuntu 22.04)
- [ ] **3단계**: 방화벽 규칙 설정 (tcp:80, tcp:443만)
  - ⚠️ tcp:5050은 공개하지 말 것
- [ ] **4단계**: SSH 접속 및 시스템 패키지 설치
  - [ ] Deadsnakes PPA 추가 (python3.11)
  - [ ] Git, FFmpeg, Graphviz
  - [ ] Miniconda (Conda 사용 시 - 추천)
- [ ] **5단계**: 코드 업로드 (GitHub/SCP)
- [ ] **6단계**: Python 환경 설정
  - [ ] Conda: `conda env create -f environment_crossplatform.yml`
  - [ ] pip: `pip install -r requirements_crossplatform.txt`
  - [ ] LangChain 1.0.5 버전 확인
- [ ] **7단계**: .env 파일 설정
  - [ ] GOOGLE_API_KEY, OPENAI_API_KEY
  - [ ] Firebase 설정 (13개 항목)
  - [ ] FIREBASE_STORAGE_BUCKET: `your_project_id.appspot.com` 형식
  - [ ] FLASK_SECRET_KEY 생성
  - [ ] ADMIN_EMAILS
- [ ] **8단계**: 데이터베이스 초기화 (`python init_db.py`)
- [ ] **9단계**: Gunicorn 설치
  - [ ] `pip install gunicorn`
  - [ ] 테스트 실행 확인
- [ ] **10단계**: systemd 서비스 등록
  - [ ] Gunicorn으로 실행 (127.0.0.1:5050)
  - [ ] EnvironmentFile 설정
  - [ ] 로그 디렉토리 생성
  - [ ] 서비스 시작 및 확인
- [ ] **11단계**: Nginx 리버스 프록시 설정
  - [ ] Nginx 설치
  - [ ] 리버스 프록시 설정 (80 → 5050)
  - [ ] SSE 지원 설정
- [ ] **12단계**: 외부 IP로 접속 확인
  - [ ] http://[외부_IP] 접속
  - ⚠️ Firebase 인증은 도메인 필요

### 선택 단계

- [ ] HTTPS 설정 (Let's Encrypt)
- [ ] 도메인 연결
- [ ] 자동 백업 설정 (cron)
- [ ] Cloud Storage 백업
- [ ] LangSmith 트레이싱 활성화

### 문제 발생 시 확인 사항

```bash
# 서비스 상태
sudo systemctl status minute-ai

# 로그 확인
sudo journalctl -u minute-ai -n 100 --no-pager

# Python 환경 확인
which python
python --version
pip list | grep langchain

# 데이터베이스 확인
ls -lh database/minute_ai.db
sqlite3 database/minute_ai.db "SELECT name FROM sqlite_master WHERE type='table';"

# 포트 리스닝 확인
sudo netstat -tulpn | grep 5050
```

---

## 📝 변경 이력

**버전 2.1** (2025-11-10) - 프로덕션 배포 보안 강화
- ⚠️ **Gunicorn 사용 필수화** (Flask 내장 서버 대신)
- ⚠️ **Nginx 리버스 프록시 추가** (보안 강화)
- ⚠️ **방화벽 규칙 수정**: 80/443만 공개, 5050 내부만
- ⚠️ **Firebase 제약사항 명시**: IP 주소 불가, 도메인 필수
- Deadsnakes PPA로 Python 3.11 설치 (Ubuntu 22.04)
- FIREBASE_STORAGE_BUCKET 형식 수정 (`appspot.com`)
- systemd EnvironmentFile 추가 (.env 자동 로드)
- Instance Schedules로 자동 시작/중지 (크론 X)
- gsutil 설치 확인 추가
- 비용 추정치 현실화 ($35-55/월)
- Cloud Run SQLite 제약사항 강화

**버전 2.0** (2025-11-10)
- LangChain 1.0.x 업그레이드 대응
- Conda 환경 지원 추가
- requirements_crossplatform.txt 사용
- init_db.py 데이터베이스 초기화 단계 추가
- graphviz 시스템 의존성 추가
- Firebase 환경 변수 업데이트
- Python 3.11.13 명시
- 문제 해결 섹션 확장

**버전 1.0** (2025-11-08)
- 초기 버전 작성

---

**최종 업데이트**: 2025-11-10 (v2.1)
**대상 시스템**: Minute AI (AI 회의록 자동 생성 시스템)
**추천 환경**: GCP Compute Engine (e2-medium, Ubuntu 22.04) + Gunicorn + Nginx
