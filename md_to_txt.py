#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to Plain Text Converter
마크다운 문법을 제거하고 순수 텍스트로 변환합니다.
"""

import re
import sys


def remove_markdown(content):
    """마크다운 문법을 제거하여 순수 텍스트로 변환"""

    # 1. 코드 블록 제거 (``` ... ```)
    content = re.sub(r'```[^\n]*\n.*?```', lambda m: m.group(0).replace('```', '').strip(), content, flags=re.DOTALL)

    # 2. 인라인 코드 제거 (` ... `)
    content = re.sub(r'`([^`]+)`', r'\1', content)

    # 3. 볼드 제거 (** ... **)
    content = re.sub(r'\*\*([^\*]+)\*\*', r'\1', content)

    # 4. 이탤릭 제거 (* ... *)
    content = re.sub(r'\*([^\*\n]+)\*', r'\1', content)

    # 5. 헤더 제거 (# ... )
    content = re.sub(r'^#{1,6}\s+(.+)$', r'\1', content, flags=re.MULTILINE)

    # 6. 리스트 마커 제거 (-, *, +)
    content = re.sub(r'^\s*[-\*\+]\s+', '  ', content, flags=re.MULTILINE)

    # 7. 인용 제거 (>)
    content = re.sub(r'^>\s+', '', content, flags=re.MULTILINE)

    # 8. 수평선 제거 (---)
    content = re.sub(r'^-{3,}$', '', content, flags=re.MULTILINE)

    # 9. 링크 제거 ([text](#link) 또는 [text](url))
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)

    # 10. 체크박스 제거 (- [ ] or - [x])
    content = re.sub(r'^\s*\[([ x])\]\s+', '', content, flags=re.MULTILINE)

    # 11. 테이블 구분선 제거 (|-----|)
    content = re.sub(r'^\s*\|[\-\:\s\|]+\|\s*$', '', content, flags=re.MULTILINE)

    # 12. 테이블 파이프를 공백으로 변환
    content = re.sub(r'\s*\|\s*', '  ', content)

    # 13. 이모지 체크/크로스 제거
    content = re.sub(r'[✅❌⚠️]', '', content)

    # 14. 여러 빈 줄을 최대 2개로 제한
    content = re.sub(r'\n{3,}', '\n\n', content)

    # 15. 줄 끝 공백 제거
    content = re.sub(r'[ \t]+$', '', content, flags=re.MULTILINE)

    return content


def convert_md_to_txt(md_file, txt_file=None):
    """마크다운 파일을 텍스트 파일로 변환"""

    if txt_file is None:
        txt_file = md_file.replace('.md', '.txt')

    print(f"📄 변환 시작: {md_file}")

    try:
        # 마크다운 파일 읽기
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 마크다운 문법 제거
        plain_text = remove_markdown(content)

        # 텍스트 파일로 저장
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(plain_text)

        print(f"✅ 텍스트 파일 생성 완료: {txt_file}")

        # 파일 정보 출력
        lines = plain_text.count('\n') + 1
        chars = len(plain_text)
        print(f"📊 총 {lines:,}줄, {chars:,}자")

        return True

    except Exception as e:
        print(f"❌ 변환 실패: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("사용법: python md_to_txt.py <markdown_file.md> [output.txt]")
        print("\n예시:")
        print("  python md_to_txt.py 심사위원_예상질문_50선.md")
        print("  python md_to_txt.py input.md output.txt")
        return

    md_file = sys.argv[1]
    txt_file = sys.argv[2] if len(sys.argv) > 2 else None

    convert_md_to_txt(md_file, txt_file)


if __name__ == "__main__":
    main()
