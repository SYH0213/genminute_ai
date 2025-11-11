#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to PDF Converter
한글 지원이 포함된 마크다운 문서를 PDF로 변환합니다.
"""

import os
import sys
import markdown
from weasyprint import HTML, CSS
from pathlib import Path


def convert_md_to_pdf(md_file_path, output_pdf_path=None):
    """
    마크다운 파일을 PDF로 변환

    Args:
        md_file_path: 입력 마크다운 파일 경로
        output_pdf_path: 출력 PDF 파일 경로 (None이면 자동 생성)
    """

    # 파일 존재 확인
    if not os.path.exists(md_file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {md_file_path}")
        return False

    # 출력 경로 설정
    if output_pdf_path is None:
        output_pdf_path = md_file_path.replace('.md', '.pdf')

    print(f"📄 변환 시작: {md_file_path}")

    try:
        # 마크다운 파일 읽기
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # 마크다운을 HTML로 변환
        html_content = markdown.markdown(
            md_content,
            extensions=[
                'extra',  # 테이블, 코드 블록 등 추가 기능
                'nl2br',  # 줄바꿈 자동 변환
                'sane_lists',  # 리스트 처리 개선
            ]
        )

        # HTML 템플릿 생성 (한글 폰트 지원)
        html_template = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 2cm 1.5cm;
                    @bottom-center {{
                        content: counter(page) " / " counter(pages);
                        font-size: 10pt;
                        color: #666;
                    }}
                }}

                body {{
                    font-family: "Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
                    font-size: 11pt;
                    line-height: 1.6;
                    color: #333;
                    max-width: 100%;
                    word-wrap: break-word;
                }}

                h1 {{
                    font-size: 24pt;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-top: 0;
                    margin-bottom: 0.5em;
                    padding-bottom: 0.3em;
                    border-bottom: 3px solid #3498db;
                    page-break-before: avoid;
                }}

                h2 {{
                    font-size: 18pt;
                    font-weight: bold;
                    color: #34495e;
                    margin-top: 1.5em;
                    margin-bottom: 0.5em;
                    padding-left: 0.3em;
                    border-left: 4px solid #3498db;
                    page-break-after: avoid;
                }}

                h3 {{
                    font-size: 14pt;
                    font-weight: bold;
                    color: #555;
                    margin-top: 1.2em;
                    margin-bottom: 0.4em;
                    page-break-after: avoid;
                }}

                h4 {{
                    font-size: 12pt;
                    font-weight: bold;
                    color: #666;
                    margin-top: 1em;
                    margin-bottom: 0.3em;
                }}

                p {{
                    margin: 0.5em 0;
                    text-align: justify;
                }}

                strong {{
                    color: #2c3e50;
                    font-weight: bold;
                }}

                em {{
                    color: #e74c3c;
                    font-style: normal;
                    font-weight: 500;
                }}

                code {{
                    font-family: "Consolas", "Monaco", "Courier New", monospace;
                    font-size: 10pt;
                    background-color: #f5f5f5;
                    padding: 2px 5px;
                    border-radius: 3px;
                    color: #e74c3c;
                }}

                pre {{
                    background-color: #f8f8f8;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    overflow-x: auto;
                    font-size: 9pt;
                    line-height: 1.4;
                    page-break-inside: avoid;
                }}

                pre code {{
                    background-color: transparent;
                    padding: 0;
                    color: #333;
                }}

                ul, ol {{
                    margin: 0.5em 0;
                    padding-left: 1.5em;
                }}

                li {{
                    margin: 0.3em 0;
                }}

                blockquote {{
                    border-left: 4px solid #3498db;
                    padding-left: 1em;
                    margin-left: 0;
                    color: #555;
                    font-style: italic;
                    background-color: #f9f9f9;
                    padding: 0.5em 1em;
                    border-radius: 3px;
                }}

                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 1em 0;
                    page-break-inside: avoid;
                }}

                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}

                th {{
                    background-color: #3498db;
                    color: white;
                    font-weight: bold;
                }}

                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}

                hr {{
                    border: none;
                    border-top: 2px solid #ddd;
                    margin: 2em 0;
                }}

                /* 페이지 나누기 제어 */
                .page-break {{
                    page-break-before: always;
                }}

                /* 질문 답변 스타일 */
                h3[id^="q"] {{
                    background-color: #ecf0f1;
                    padding: 0.5em;
                    border-radius: 5px;
                    border-left: 4px solid #e74c3c;
                }}

                /* 인쇄 최적화 */
                @media print {{
                    body {{
                        font-size: 10pt;
                    }}
                    h1 {{
                        font-size: 22pt;
                    }}
                    h2 {{
                        font-size: 16pt;
                    }}
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # HTML을 PDF로 변환
        print("🔄 PDF 생성 중...")
        HTML(string=html_template).write_pdf(
            output_pdf_path,
            stylesheets=None,
            presentational_hints=True
        )

        print(f"✅ PDF 변환 완료: {output_pdf_path}")

        # 파일 크기 확인
        file_size = os.path.getsize(output_pdf_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"📊 파일 크기: {file_size_mb:.2f} MB")

        return True

    except Exception as e:
        print(f"❌ PDF 변환 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수"""

    if len(sys.argv) < 2:
        print("사용법: python convert_md_to_pdf.py <markdown_file.md> [output.pdf]")
        print("\n예시:")
        print("  python convert_md_to_pdf.py 심사위원_예상질문_50선.md")
        print("  python convert_md_to_pdf.py input.md output.pdf")
        return

    md_file = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else None

    # 절대 경로로 변환
    md_file = os.path.abspath(md_file)
    if output_pdf:
        output_pdf = os.path.abspath(output_pdf)

    # 변환 실행
    success = convert_md_to_pdf(md_file, output_pdf)

    if success:
        print("\n✨ 변환이 성공적으로 완료되었습니다!")
    else:
        print("\n❌ 변환 중 오류가 발생했습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
