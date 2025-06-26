import google.generativeai as genai
import os
import json # json 라이브러리 추가

# 환경변수에서 Gemini API Key를 불러옵니다.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def extract_timestamps_json(video_path: str, analysis_result: dict) -> dict:
    """
    입력:
        - video_path: 원본 영상 파일 경로 (str)
        - analysis_result: 1차 분석 결과 (dict, 예: 사고 개요 등)
    출력:
        - 타임스탬프별 사건 리스트 dict
    """
    # 1. 프롬프트 생성 (개선안 2: JSON 출력 요청)
    prompt = f"""
    ## 당신의 역할
    - 당신은 교통사고 분석 보고서를 이해하고, 주요 사건들을 구조화된 JSON 형식으로 추출하는 유용한 조수입니다.

    ## 작업
    - 아래에 제공된 [1차 분석 결과]를 바탕으로 시간 순서에 따른 사건 목록을 생성합니다.
    - 각 사건은 반드시 시작 시간, 종료 시간, 그리고 사건에 대한 설명을 포함해야 합니다.
    - 당신의 전체 출력은 반드시 단일 JSON 객체여야 합니다.

    ## 출력 형식 명세
    - JSON 객체의 최상위 키는 "events"여야 합니다.
    - "events"의 값은 사건 객체들이 담긴 배열이어야 합니다.
    - 배열에 포함된 각 사건 객체는 "start", "end", "description"이라는 세 개의 문자열 키를 가져야 합니다.
    - "start"와 "end"의 시간 형식은 "MM:SS"여야 합니다.
    - **중요:** JSON 객체 외에는 아무것도 출력하지 마세요. 마크다운 백틱(```json ... ```)이나 다른 설명 텍스트를 포함해서는 안 됩니다.

    ## 1차 분석 결과
    {analysis_result}

    ## 출력 예시
    {{
        "events": [
            {{"start": "00:01", "end": "00:03", "description": "블랙박스 차량이 아파트 단지에서 출발합니다."}},
            {{"start": "00:04", "end": "00:06", "description": "우회전하여 일반 도로로 진입합니다."}},
            {{"start": "00:07", "end": "00:08", "description": "1차선으로 차선을 변경합니다."}},
            {{"start": "00:10", "end": "00:11", "description": "전방 차량과 추돌합니다."}}
        ]
    }}
    """

    # 2. Gemini API 호출
    if not GOOGLE_API_KEY:
        return {
            "events": [
                {"start": "00:00", "end": "00:00", "description": "(API Key not found) Example JSON result"}
            ]
        }
    try:
        # JSON 출력을 지원하는 최신 모델 사용을 권장합니다.
        model = genai.GenerativeModel(
            "gemini-2.5-pro",
            generation_config={"response_mime_type": "application/json"} # JSON 출력 모드 활성화
        )
        response = model.generate_content(prompt)

        # 3. 결과 파싱 (JSON)
        # Gemini가 생성한 텍스트가 순수한 JSON 문자열이라고 가정합니다.
        # response.text에 JSON 문자열이 들어있습니다.
        return json.loads(response.text)

    except json.JSONDecodeError as e:
        # 모델이 유효하지 않은 JSON을 반환한 경우
        return {"events": [{"start": "", "end": "", "description": f"JSON Parsing Error: {e}. Raw response: {response.text}"}]}
    except Exception as e:
        return {"events": [{"start": "", "end": "", "description": f"Gemini API Error: {e}"}]}