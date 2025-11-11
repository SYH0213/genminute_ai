#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to PDF Converter
마크다운 파일을 PDF로 변환합니다.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_pandoc():
    """pandoc이 설치되어 있는지 확인"""
    try:
        result = subprocess.run(
            ['pandoc', '--version'],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def convert_md_to_pdf_pandoc(md_file, output_pdf=None):
    """
    pandoc을 사용하여 마크다운을 PDF로 변환

    Args:
        md_file: 입력 마크다운 파일 경로
        output_pdf: 출력 PDF 파일 경로 (None이면 자동 생성)
    """
    if not os.path.exists(md_file):
        print(f"❌ 파일을 찾을 수 없습니다: {md_file}")
        return False

    if output_pdf is None:
        output_pdf = md_file.replace('.md', '.pdf')

    print(f"📄 변환 시작: {md_file}")
    print(f"📝 출력 경로: {output_pdf}")

    # pandoc 명령어 구성
    # --pdf-engine=xelatex : 한글 지원을 위한 XeLaTeX 사용
    # -V geometry:margin=2cm : 페이지 여백 설정
    # -V mainfont="Malgun Gothic" : 한글 폰트 설정 (Windows)
    # --toc : 목차 생성
    cmd = [
        'pandoc',
        md_file,
        '-o', output_pdf,
        '--pdf-engine=xelatex',
        '-V', 'geometry:margin=2cm',
        '-V', 'fontsize=11pt',
        '-V', 'linestretch=1.5',
        '--toc',
        '--toc-depth=3',
        '--highlight-style=tango'
    ]

    # 운영체제에 따라 폰트 설정
    if sys.platform == 'win32':
        cmd.extend(['-V', 'mainfont="Malgun Gothic"'])
        cmd.extend(['-V', 'CJKmainfont="Malgun Gothic"'])
    elif sys.platform == 'darwin':  # macOS
        cmd.extend(['-V', 'mainfont="Apple SD Gothic Neo"'])
        cmd.extend(['-V', 'CJKmainfont="Apple SD Gothic Neo"'])
    else:  # Linux
        cmd.extend(['-V', 'mainfont="Noto Sans CJK KR"'])
        cmd.extend(['-V', 'CJKmainfont="Noto Sans CJK KR"'])

    try:
        print("🔄 PDF 생성 중...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        if os.path.exists(output_pdf):
            file_size = os.path.getsize(output_pdf)
            file_size_mb = file_size / (1024 * 1024)
            print(f"✅ PDF 변환 완료!")
            print(f"📊 파일 크기: {file_size_mb:.2f} MB")
            print(f"📂 저장 위치: {os.path.abspath(output_pdf)}")
            return True
        else:
            print("❌ PDF 파일이 생성되지 않았습니다.")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ PDF 변환 실패:")
        print(f"   {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False


def main():
    """메인 함수"""

    print("=" * 60)
    print("📚 Markdown to PDF Converter")
    print("=" * 60)

    # pandoc 설치 확인
    if not check_pandoc():
        print("\n❌ pandoc이 설치되어 있지 않습니다.")
        print("\n📥 설치 방법:")
        print("   Windows: https://pandoc.org/installing.html")
        print("   또는: winget install pandoc")
        print("   또는: choco install pandoc")
        print("\n   Linux: sudo apt-get install pandoc texlive-xetex")
        print("   macOS: brew install pandoc basictex")
        return

    print("✅ pandoc이 설치되어 있습니다.\n")

    # 명령행 인자 처리
    if len(sys.argv) < 2:
        print("사용법: python md_to_pdf.py <markdown_file.md> [output.pdf]")
        print("\n예시:")
        print("  python md_to_pdf.py 심사위원_예상질문_50선.md")
        print("  python md_to_pdf.py input.md output.pdf")
        print("\n📁 현재 디렉토리의 .md 파일:")

        # 현재 디렉토리의 마크다운 파일 목록 표시
        md_files = list(Path('.').glob('*.md'))
        md_files.extend(Path('markdown_folder/발표_QA준비').glob('*.md') if Path('markdown_folder/발표_QA준비').exists() else [])

        if md_files:
            for i, f in enumerate(md_files[:10], 1):
                print(f"  {i}. {f}")
        else:
            print("  (없음)")

        return

    md_file = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else None

    # 절대 경로로 변환
    md_file = os.path.abspath(md_file)
    if output_pdf:
        output_pdf = os.path.abspath(output_pdf)

    # 변환 실행
    success = convert_md_to_pdf_pandoc(md_file, output_pdf)

    print("\n" + "=" * 60)
    if success:
        print("✨ 변환이 성공적으로 완료되었습니다!")
    else:
        print("❌ 변환 중 오류가 발생했습니다.")
        sys.exit(1)
    print("=" * 60)


if __name__ == "__main__":
    main()
