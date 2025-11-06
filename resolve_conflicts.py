"""
Git 충돌 자동 해결 스크립트
HEAD (새로운 보안 수정) 코드를 유지하고 이전 커밋 코드는 제거
"""

def resolve_conflict_file(filepath):
    """충돌 마커를 찾아서 HEAD 쪽 코드만 유지"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    resolved_lines = []
    in_conflict = False
    keep_section = False

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith('<<<<<<< HEAD'):
            # 충돌 시작 - HEAD 쪽 코드 유지
            in_conflict = True
            keep_section = True
        elif line.startswith('======='):
            # 구분선 - 이제부터는 버릴 코드
            keep_section = False
        elif line.startswith('>>>>>>>'):
            # 충돌 종료
            in_conflict = False
            keep_section = False
        else:
            # 일반 라인
            if not in_conflict:
                # 충돌 밖의 코드는 모두 유지
                resolved_lines.append(line)
            elif keep_section:
                # 충돌 안에서 HEAD 쪽 코드만 유지
                resolved_lines.append(line)
            # else: 버리는 섹션은 추가하지 않음

        i += 1

    # 파일에 다시 쓰기
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(resolved_lines)

    print(f"✅ {filepath} 충돌 해결 완료")

# 충돌이 있는 파일들
files = [
    'app.py',
    'utils/user_manager.py',
    'templates/login.html'
]

print("🔧 Git 충돌 해결 시작...\n")

for file in files:
    try:
        resolve_conflict_file(file)
    except Exception as e:
        print(f"❌ {file} 처리 실패: {e}")

print("\n🎉 모든 충돌 해결 완료!")
print("\n다음 명령어로 확인하세요:")
print("  git status")
print("  git diff")
