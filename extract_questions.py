#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
질문만 추출하기
마크다운 파일에서 Q1~Q50 질문만 추출합니다.
"""

import re
import sys


def extract_questions(md_file, output_file=None):
    """마크다운 파일에서 질문만 추출"""

    if output_file is None:
        output_file = md_file.replace('.md', '_질문만.txt')

    print(f"📄 파일 읽기: {md_file}")

    try:
        # 마크다운 파일 읽기
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Q숫자. 질문 패턴 찾기
        # ## Q1. 질문내용?
        pattern = r'^##\s+(Q\d+)\.\s+(.+?)$'
        matches = re.findall(pattern, content, flags=re.MULTILINE)

        if not matches:
            print("❌ 질문을 찾을 수 없습니다.")
            return False

        # 질문만 추출하여 텍스트 생성
        questions_text = "심사위원 예상 질문 목록\n"
        questions_text += "=" * 60 + "\n\n"

        for q_num, question in matches:
            questions_text += f"{q_num}. {question}\n\n"

        # 텍스트 파일로 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(questions_text)

        print(f"✅ 질문 추출 완료: {output_file}")
        print(f"📊 총 {len(matches)}개 질문")

        return True

    except Exception as e:
        print(f"❌ 추출 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("사용법: python extract_questions.py <markdown_file.md> [output.txt]")
        print("\n예시:")
        print("  python extract_questions.py 심사위원_예상질문_50선.md")
        print("  python extract_questions.py input.md questions.txt")
        return

    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    extract_questions(md_file, output_file)


if __name__ == "__main__":
    main()
