#!/usr/bin/env python3
"""
환경 테스트 스크립트
새로운 conda 환경(genminute_test)이 제대로 설정되었는지 확인합니다.
"""

import sys

def test_imports():
    """핵심 패키지 import 테스트"""
    print("=" * 60)
    print("🧪 패키지 Import 테스트 시작")
    print("=" * 60)

    packages = [
        ("flask", "Flask"),
        ("chromadb", "ChromaDB"),
        ("google.genai", "Google Genai"),
        ("langchain", "LangChain"),
        ("langchain_core", "LangChain Core"),
        ("langchain_openai", "LangChain OpenAI"),
        ("langchain_chroma", "LangChain Chroma"),
        ("langchain_text_splitters", "LangChain Text Splitters"),
        ("openai", "OpenAI"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("firebase_admin", "Firebase Admin"),
        ("pydot", "PyDot (마인드맵)"),
    ]

    failed = []

    for module_name, display_name in packages:
        try:
            module = __import__(module_name)
            version = getattr(module, "__version__", "N/A")
            print(f"  ✅ {display_name:25} v{version}")
        except ImportError as e:
            print(f"  ❌ {display_name:25} FAILED: {e}")
            failed.append(display_name)

    print()

    if failed:
        print(f"❌ {len(failed)}개 패키지 import 실패: {', '.join(failed)}")
        return False
    else:
        print("✅ 모든 패키지 import 성공!")
        return True


def test_versions():
    """LangChain 버전 호환성 체크"""
    print("\n" + "=" * 60)
    print("🔍 LangChain 버전 호환성 체크")
    print("=" * 60)

    try:
        import langchain
        import langchain_core
        import langchain_chroma
        import langchain_openai

        # __version__ 없는 패키지 대응
        def get_version(module):
            if hasattr(module, '__version__'):
                return module.__version__
            else:
                # importlib.metadata로 시도
                try:
                    import importlib.metadata
                    return importlib.metadata.version(module.__name__)
                except:
                    return "unknown"

        versions = {
            "langchain": get_version(langchain),
            "langchain-core": get_version(langchain_core),
            "langchain-chroma": get_version(langchain_chroma),
            "langchain-openai": get_version(langchain_openai),
        }

        for name, version in versions.items():
            print(f"  • {name:20} v{version}")

        # 버전 호환성 체크 (메이저 버전만)
        lc_version = versions["langchain"]
        lc_core_version = versions["langchain-core"]

        if lc_version == "unknown" or lc_core_version == "unknown":
            print(f"\n  ⚠️  버전 정보 불완전하지만 import는 성공 (무시 가능)")
            return True

        lc_major = int(lc_version.split('.')[0])
        lc_core_major = int(lc_core_version.split('.')[0])

        if lc_major == lc_core_major:
            print(f"\n  ✅ 호환성 OK: langchain {lc_version} ↔ langchain-core {lc_core_version}")
            return True
        else:
            print(f"\n  ⚠️  버전 미스매치: langchain {lc_version} ↔ langchain-core {lc_core_version}")
            return False

    except Exception as e:
        print(f"  ❌ 버전 체크 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_app_config():
    """앱 설정 파일 존재 확인"""
    print("\n" + "=" * 60)
    print("📁 앱 설정 파일 확인")
    print("=" * 60)

    import os

    required_files = [
        ".env",
        "database/minute_ai.db",
        "uploads",
    ]

    optional_files = [
        "firebase/credentials.json",
    ]

    all_ok = True

    for filepath in required_files:
        if os.path.exists(filepath):
            print(f"  ✅ {filepath}")
        else:
            print(f"  ❌ {filepath} (필수)")
            all_ok = False

    for filepath in optional_files:
        if os.path.exists(filepath):
            print(f"  ✅ {filepath} (선택)")
        else:
            print(f"  ⚠️  {filepath} (선택, 없으면 인증 불가)")

    return all_ok


def main():
    """메인 테스트 실행"""
    print("\n🚀 genminute_test 환경 테스트 시작\n")

    results = {
        "패키지 Import": test_imports(),
        "버전 호환성": test_versions(),
        "앱 설정": test_app_config(),
    }

    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name:15} {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 모든 테스트 통과! 환경이 정상적으로 설정되었습니다.")
        print("다음 명령으로 앱을 실행하세요:")
        print("  python app.py")
    else:
        print("⚠️  일부 테스트 실패. 위의 오류를 확인하세요.")
        sys.exit(1)
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
