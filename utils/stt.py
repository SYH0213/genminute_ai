import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
class STTManager:
    def __init__(self):
        load_dotenv() # 환경 변수 로드

    @staticmethod
    def _parse_mmss_to_seconds(time_str):
        """
        '분:초:밀리초' 형태의 문자열을 초 단위로 변환합니다.
        """
        try:
            parts = time_str.split(":")
            if len(parts) == 3:
                minutes = int(parts[0])
                seconds = int(parts[1])
                milliseconds = int(parts[2])
                return minutes * 60 + seconds + milliseconds / 1000.0
            else:
                return 0.0
        except:
            return 0.0

    def transcribe_audio(self, audio_path):
        """Google Gemini STT API로 음성 인식"""
        try:
            print(f"🎧 Gemini STT API로 음성 인식 중: {audio_path}")
            api_key = os.environ.get("GOOGLE_API_KEY")
            if api_key:
                client = genai.Client(api_key=api_key)
            else:
                client = genai.Client()

            with open(audio_path, "rb") as f:
                file_bytes = f.read()

            file_ext = os.path.splitext(audio_path)[1].lower()
            mime_type_map = {
                ".wav": "audio/wav", ".mp3": "audio/mp3",
                ".m4a": "audio/mp4", ".flac": "audio/flac",
            }
            mime_type = mime_type_map.get(file_ext, "audio/wav")

            prompt = """
당신은 전문적인 회의록 작성자입니다. 제공된 오디오 파일을 듣고 다음 작업을 수행해 주십시오:
1. 전체 대화를 정확하게 텍스트로 변환합니다.
2. 각 발화에 대해 화자를 숫자로 구분합니다. 발화자의 등장 순서대로 번호를 할당합니다.
3. 각 발화에 대해 음성 인식의 신뢰도를 0.0~1.0 사이의 값으로 평가합니다.
4. 최종 결과는 아래의 JSON 형식과 정확히 일치해야 합니다. 각 JSON 객체는 'speaker', 'start_time_mmss', 'confidence', 'text' 키를 포함해야 합니다.
5. start_time_mmss는 "분:초:밀리초" 형태로 출력합니다. (예: "0:05:200", "1:23:450")

출력 형식:
[
    {
        "speaker": 1,
        "start_time_mmss": "0:00:000",
        "confidence": 0.95,
        "text": "안녕하세요. 회의를 시작하겠습니다."
    },
    {
        "speaker": 2,
        "start_time_mmss": "0:05:200",
        "confidence": 0.92,
        "text": "네, 좋습니다."
    }
]

JSON 배열만 출력하고, 추가 설명이나 마크다운 코드 블록은 포함하지 마세요.
"""

            print("🤖 Gemini 2.5 Pro로 음성 인식 중...")
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[prompt, types.Part.from_bytes(data=file_bytes, mime_type=mime_type)],
            )

            cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
            result_list = json.loads(cleaned_response)

            normalized_segments = []
            for idx, segment in enumerate(result_list):
                normalized_segments.append({
                    "id": idx,
                    "speaker": segment.get("speaker", 1),
                    "start_time": self._parse_mmss_to_seconds(segment.get("start_time_mmss", "0:00:000")),
                    "confidence": segment.get("confidence", 0.0),
                    "text": segment.get("text", ""),
                })
            print("✅ Gemini 음성 인식 완료")
            return normalized_segments

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Gemini 오류 발생: {e}")
            return None

    def subtopic_generate(self, title: str, transcript_text: str):
        prompt_text = f"""당신은 제공된 대화 스크립트 내용을 분석하여, 구조화된 주제별 요약본으로 변환하는 AI 어시스턴트입니다.

            **입력 파일 형식:**
            입력 내용은 여러 화자(1,2,3,...)가 참여하는 원본 대화 내용입니다.

            **출력 요구사항:**
            당신은 입력 파일을 다음과 같은 규칙에 따라 요약본으로 변환해야 합니다.

            1.  회의 제목 : {title}
            2.  주제별 그룹화 : 스크립트 전체 내용을 분석하여 주요 논의 주제를 파악합니다.
            3.  소주제 제목 형식 (중요): 각 주요 주제별로 핵심 내용을 요약하는 제목을 **반드시 "### 제목" 형식**으로 생성합니다. (예: `### 대주주 주식 양도세 기준 논란`)
            4.  내용 요약: 각 주제 제목 아래에 관련된 핵심 주장, 사실, 의견을 글머리 기호(`*`)를 사용하여 요약합니다.
            5.  문체 변환: 원본의 구어체(대화체)를 간결하고 공식적인 서술형 문어체(요약문 스타일)로 변경합니다.
            6.  화자 및 군더더기 제거: 'A:', 'B:'와 같은 화자 표시와 '그러니까', '어,', '자,', '[웃음]' 등 대화의 군더더기를 모두 제거하고 내용만 정제하여 요약합니다.
            7.  제목과 내용 간격: 소주제 제목(### 제목)과 첫 번째 글머리 기호(*) 사이에는 공백 줄을 두지 않습니다. 제목 바로 다음 줄에 내용을 작성합니다.
            8.  문단 간격: 서로 다른 소주제 사이에는 줄바꿈을 2개 넣어 가독성을 높입니다.
            9.  정확한 인용 (필수):
                * 요약된 모든 문장이나 구절 끝에는 반드시 원본 스크립트의 번호를 형식으로 변환하여 삽입해야 합니다.
                * 하나의 글머리 기호가 여러 소스의 내용을 종합한 경우, 모든 관련 소스 번호를 인용해야 합니다. [cite_start](예: `[cite: 1, 2]`)
                * 인용은 요약된 내용과 원본 소스 간의 사실 관계가 정확히 일치해야 합니다.

            **출력 예시:**
            ### 첫 번째 주요 주제
            * 첫 번째 논의 내용 요약 [cite: 1]
            * 두 번째 논의 내용 요약 [cite: 2, 3]

            ### 두 번째 주요 주제
            * 관련 논의 내용 요약 [cite: 4]

            작업 수행:
            이제 다음 [스크립트 내용]을 분석하여 위의 요구사항을 모두 준수하는 주제별 요약본을 생성해 주십시오.
            {transcript_text}"""
        
        print(f"======prompt_text========")
        print(prompt_text)

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY가 .env 파일에 설정되지 않았습니다.")

        client = genai.Client(api_key=api_key)
        model = "gemini-2.5-pro"

        print("🤖 Gemini를 통해 요약 생성 중...")
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=prompt_text),
                        ],
                    ),
                ],
            )
            summary_content = response.text.strip()
            print("✅ Gemini 요약 생성 완료.")
            return summary_content
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Gemini 요약 생성 중 오류 발생: {e}")
            return None
        



