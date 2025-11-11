#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
마크다운을 HTML로 변환 (Word에서 열기 위한 형식)
"""

import re
import sys


def markdown_to_html(md_file, html_file=None):
    """마크다운을 Word 호환 HTML로 변환"""

    if html_file is None:
        html_file = md_file.replace('.md', '.html')

    print(f"📄 파일 읽기: {md_file}")

    try:
        # 마크다운 파일 읽기
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # HTML 시작
        html = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>백엔드 핵심 정리</title>
    <style>
        body {
            font-family: "Malgun Gothic", "맑은 고딕", "Apple SD Gothic Neo", sans-serif;
            line-height: 1.8;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            background: #fff;
            color: #333;
        }

        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 40px;
        }

        h2 {
            color: #2980b9;
            border-left: 4px solid #3498db;
            padding-left: 10px;
            margin-top: 30px;
        }

        h3 {
            color: #34495e;
            margin-top: 20px;
        }

        h4 {
            color: #555;
        }

        p {
            margin: 10px 0;
        }

        ul, ol {
            margin: 10px 0;
            padding-left: 30px;
        }

        li {
            margin: 5px 0;
        }

        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Consolas", "Monaco", monospace;
            color: #e74c3c;
            font-size: 0.9em;
        }

        pre {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            line-height: 1.5;
        }

        pre code {
            background: transparent;
            color: #ecf0f1;
            padding: 0;
        }

        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin: 15px 0;
            color: #555;
            background: #f9f9f9;
            padding: 10px 15px;
            border-radius: 3px;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }

        th {
            background: #3498db;
            color: white;
            font-weight: bold;
        }

        tr:nth-child(even) {
            background: #f9f9f9;
        }

        strong {
            color: #2c3e50;
            font-weight: bold;
        }

        hr {
            border: none;
            border-top: 2px solid #ddd;
            margin: 30px 0;
        }

        .highlight {
            background: #fff3cd;
            padding: 2px 5px;
            border-radius: 3px;
        }

        @media print {
            body {
                max-width: 100%;
            }
        }
    </style>
</head>
<body>
"""

        # 마크다운 변환
        lines = content.split('\n')
        in_code_block = False
        in_table = False

        for line in lines:
            # 코드 블록
            if line.startswith('```'):
                if in_code_block:
                    html += '</code></pre>\n'
                    in_code_block = False
                else:
                    html += '<pre><code>'
                    in_code_block = True
                continue

            if in_code_block:
                html += line + '\n'
                continue

            # 헤더
            if line.startswith('# '):
                html += f'<h1>{line[2:]}</h1>\n'
            elif line.startswith('## '):
                html += f'<h2>{line[3:]}</h2>\n'
            elif line.startswith('### '):
                html += f'<h3>{line[4:]}</h3>\n'
            elif line.startswith('#### '):
                html += f'<h4>{line[5:]}</h4>\n'

            # 인용
            elif line.startswith('> '):
                html += f'<blockquote>{line[2:]}</blockquote>\n'

            # 수평선
            elif line.startswith('---') or line.startswith('***'):
                html += '<hr>\n'

            # 테이블
            elif '|' in line and not line.startswith('|---'):
                if not in_table:
                    html += '<table>\n'
                    in_table = True
                    # 헤더 행
                    cells = [c.strip() for c in line.split('|')[1:-1]]
                    html += '<tr>'
                    for cell in cells:
                        html += f'<th>{cell}</th>'
                    html += '</tr>\n'
                else:
                    # 데이터 행
                    cells = [c.strip() for c in line.split('|')[1:-1]]
                    html += '<tr>'
                    for cell in cells:
                        html += f'<td>{cell}</td>'
                    html += '</tr>\n'
            elif in_table and not '|' in line:
                html += '</table>\n'
                in_table = False

            # 리스트
            elif re.match(r'^\d+\.\s', line):
                # 순서 있는 리스트
                text = re.sub(r'^\d+\.\s', '', line)
                html += f'<li>{text}</li>\n'
            elif line.startswith('- ') or line.startswith('* '):
                # 순서 없는 리스트
                text = line[2:]
                html += f'<li>{text}</li>\n'

            # 빈 줄
            elif not line.strip():
                html += '<br>\n'

            # 일반 텍스트
            else:
                # 볼드
                line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                # 이탤릭
                line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
                # 인라인 코드
                line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)

                html += f'<p>{line}</p>\n'

        # 테이블 닫기
        if in_table:
            html += '</table>\n'

        # HTML 끝
        html += """
</body>
</html>
"""

        # HTML 파일 저장
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML 파일 생성 완료: {html_file}")
        print(f"\n사용 방법:")
        print(f"1. {html_file} 파일을 브라우저에서 열기")
        print(f"2. Ctrl+A로 전체 선택")
        print(f"3. Ctrl+C로 복사")
        print(f"4. Word에 붙여넣기 (Ctrl+V)")
        print(f"\n또는")
        print(f"1. Word에서 '파일 > 열기'")
        print(f"2. {html_file} 선택")
        print(f"3. Word 문서로 저장")

        return True

    except Exception as e:
        print(f"❌ 변환 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("사용법: python md_to_html.py <markdown_file.md> [output.html]")
        print("\n예시:")
        print("  python md_to_html.py 백엔드_핵심정리.md")
        return

    md_file = sys.argv[1]
    html_file = sys.argv[2] if len(sys.argv) > 2 else None

    markdown_to_html(md_file, html_file)


if __name__ == "__main__":
    main()
