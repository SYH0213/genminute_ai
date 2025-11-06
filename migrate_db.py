"""
데이터베이스 마이그레이션 스크립트
- users 테이블 생성
- meeting_shares 테이블 생성
- meeting_dialogues에 owner_id 추가
- meeting_minutes에 owner_id 추가
"""

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = "database/minute_ai.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 70)
    print("🔄 데이터베이스 마이그레이션 시작")
    print("=" * 70)

    # 1. users 테이블 생성
    print("\n1️⃣ users 테이블 생성...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                google_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                profile_picture TEXT,
                role TEXT DEFAULT 'user',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("✅ users 테이블 생성 완료")
    except Exception as e:
        print(f"❌ 에러: {e}")

    # 2. meeting_shares 테이블 생성
    print("\n2️⃣ meeting_shares 테이블 생성...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meeting_shares (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id TEXT NOT NULL,
                owner_id INTEGER NOT NULL,
                shared_with_user_id INTEGER NOT NULL,
                permission TEXT DEFAULT 'read',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(id),
                FOREIGN KEY (shared_with_user_id) REFERENCES users(id),
                UNIQUE(meeting_id, shared_with_user_id)
            )
        """)
        conn.commit()
        print("✅ meeting_shares 테이블 생성 완료")
    except Exception as e:
        print(f"❌ 에러: {e}")

    # 3. meeting_dialogues에 owner_id 추가
    print("\n3️⃣ meeting_dialogues.owner_id 컬럼 추가...")
    try:
        cursor.execute("ALTER TABLE meeting_dialogues ADD COLUMN owner_id INTEGER")
        conn.commit()
        print("✅ owner_id 컬럼 추가 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  owner_id 컬럼이 이미 존재합니다")
        else:
            print(f"❌ 에러: {e}")

    # 4. meeting_minutes에 owner_id 추가
    print("\n4️⃣ meeting_minutes.owner_id 컬럼 추가...")
    try:
        cursor.execute("ALTER TABLE meeting_minutes ADD COLUMN owner_id INTEGER")
        conn.commit()
        print("✅ owner_id 컬럼 추가 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("⚠️  owner_id 컬럼이 이미 존재합니다")
        else:
            print(f"❌ 에러: {e}")

    # 5. Admin 사용자 생성
    print("\n5️⃣ Admin 사용자 생성...")
    admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
    admin_emails = [email.strip() for email in admin_emails if email.strip()]

    if admin_emails:
        for email in admin_emails:
            try:
                cursor.execute("""
                    INSERT INTO users (google_id, email, name, role)
                    VALUES (?, ?, ?, 'admin')
                """, (f"admin_{email}", email, "Admin User"))
                conn.commit()
                print(f"✅ Admin 사용자 생성: {email}")
            except sqlite3.IntegrityError:
                print(f"⚠️  이미 존재: {email}")
    else:
        print("⚠️  ADMIN_EMAILS 환경변수가 설정되지 않았습니다")

    # 6. 최종 확인
    print("\n" + "=" * 70)
    print("📊 테이블 확인:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for t in tables:
        print(f"  ✅ {t[0]}")

    print("\n🎉 마이그레이션 완료!")
    print("=" * 70)

    conn.close()

if __name__ == "__main__":
    migrate()
