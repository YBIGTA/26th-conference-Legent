import google.generativeai as genai
import os
import json
import cv2
import random

# 환경변수에서 Gemini API Key를 불러옵니다.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def get_video_info(video_path: str) -> dict:
    """영상 파일의 기본 정보를 추출합니다."""
    try:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        return {
            "duration": round(duration, 2),
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height
        }
    except Exception as e:
        return {
            "duration": 0,
            "fps": 0,
            "frame_count": 0,
            "width": 0,
            "height": 0,
            "error": str(e)
        }


def create_final_timeline(script_tts_info: dict, video_path: str) -> dict:
    """
    입력:
        - script_tts_info: Phase 4에서 생성된 스크립트+TTS 정보 (dict)
            {
                "scene_audio_files": [
                    {"scene": 1, "audio_path": "...", "duration_sec": 10.5, "narration": "...", "visual": "..."},
                    ...
                ],
                "total_duration": 18.8,
                "manifest_path": "..."
            }
        - video_path: 원본 영상 경로 (str)
    출력:
        - timeline_json: MoviePy용 최종 타임라인 JSON
    """
    
    # 영상 정보 가져오기
    video_info = get_video_info(video_path)
    
    # API Key가 없으면 기본 타임라인 반환
    if not GOOGLE_API_KEY:
        return create_fallback_timeline(script_tts_info, video_path, video_info)
    
    # 장면별 스크립트 데이터 준비
    scene_scripts = []
    tts_timing_data = []
    
    for scene_data in script_tts_info.get("scene_audio_files", []):
        scene_scripts.append({
            "scene_id": scene_data.get("scene", 1),
            "description": scene_data.get("visual", ""),
            "narration": scene_data.get("narration", ""),
            "text_overlay": {
                "text": "장면 " + str(scene_data.get("scene", 1)),
                "position": "bottom_center",
                "font_size": 35,
                "color": "white"
            }
        })
        
        tts_timing_data.append({
            "scene_id": scene_data.get("scene", 1),
            "tts_audio_file": scene_data.get("audio_path", ""),
            "tts_duration_sec": scene_data.get("duration_sec", 0.0)
        })
    
    # Gemini 프롬프트 생성
    prompt = f"""
# Role
당신은 Python의 MoviePy 라이브러리로 자동 편집할 수 있도록, 모든 기술적 정보와 창의적 요소를 최종 결합하는 '기술 영상 편집 AI'입니다.

# Goal
주어진 원본 영상, 장면별 스크립트, 그리고 미리 계산된 '장면별 TTS 정보'를 모두 통합하여, 영상과 음향의 싱크가 완벽하게 맞는 최종 JSON 파일을 생성합니다. 
당신의 가장 중요한 임무는 각 장면의 내용과 주어진 길이에 가장 적합한 영상의 '시작 시간(start_sec)'을 지능적으로 찾아내는 것입니다.

각 장면에는 내레이션(narration)과 시각적 설명(description)이 주어집니다.  
이 내용을 기반으로 시청자에게 자막으로 보여줄 **한 줄 요약 문장 (text_overlay["text"])**도 함께 생성해주세요.


# Input

1. **원본 영상 정보:**
   - 파일 경로: {video_path}
   - 영상 길이: {video_info.get('duration', 0)}초
   - FPS: {video_info.get('fps', 0)}
   - 해상도: {video_info.get('width', 0)}x{video_info.get('height', 0)}

2. **장면별 스크립트 (Creative Elements):**
{json.dumps(scene_scripts, ensure_ascii=False, indent=2)}

3. **장면별 TTS 정보 (Technical Timing Data):**
{json.dumps(tts_timing_data, ensure_ascii=False, indent=2)}

# Core Task: 시작 시간(start_sec) 결정 로직

각 장면의 내용을 분석하여 원본 영상에서 가장 적합한 시작 시간을 결정하세요:

1. **장면 1 (오프닝):** 사고 발생 직전의 평온한 구간부터 시작
2. **장면 2 (블박차 관점):** 블박차가 정상 주행하는 구간
3. **장면 3 (문제점 분석):** 사고 발생 순간과 그 직후
4. **장면 4 (결론/투표):** 사고 장면을 다시 보여주거나 정지 화면
5. **장면 5 (마무리):** 사고 후 상황 또는 안전 메시지용 화면

# Output Specification (JSON Schema)
아래에 명시된 최종 JSON 구조를 **반드시, 그리고 정확하게** 따라야 합니다:

```json
{{
  "video_source_file": "{video_path}",
  "title": "교통사고 분석 - 한문철TV 스타일",
  "final_liability_ratio": {{
    "car": 0,
    "bicycle": 100
  }},
  "summary_narration": "전체 사고 요약",
  "scenes": [
    {{
      "scene_id": 1,
      "description": "장면 설명",
      "source_video_timestamp": {{
        "start_sec": 0.0
      }},
      "effects": [],
      "narration": "내레이션 텍스트",
      "text_overlay": {{
        "text": "화면 텍스트",
        "position": "bottom_center",
        "font_size": 35,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 2
      }},
      "tts_audio_file": "오디오 파일 경로",no
      "tts_duration_sec": 10.5,
      "visual_padding_sec": 0.5
    }}
  ],
  "outro": {{
    "duration": 3.0,
    "background_color": [0, 0, 0],
    "text": "안전 운전하세요!",
    "narration": "마무리 메시지"
  }}
}}
```

# Critical Requirements
1. **start_sec 값들이 영상 길이({video_info.get('duration', 0)}초)를 초과하지 않도록 하세요**
2. **각 장면의 TTS 길이를 고려하여 적절한 visual_padding_sec를 설정하세요**
3. **장면 간 자연스러운 전환을 위해 시간을 배치하세요**
4. **JSON 형식을 정확히 준수하세요**

위 정보를 바탕으로 완전한 JSON 타임라인을 생성해주세요.
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # JSON 응답 파싱 시도
        try:
            # ```json 블록이 있는 경우 추출
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            timeline_data = json.loads(json_text)
            
            # 유효성 검사 및 보정
            timeline_data = validate_and_fix_timeline(timeline_data, video_info, script_tts_info)
            
            return timeline_data
            
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 실패: {e}")
            return create_fallback_timeline(script_tts_info, video_path, video_info)
            
    except Exception as e:
        print(f"Gemini API 오류: {e}")
        return create_fallback_timeline(script_tts_info, video_path, video_info)


def validate_and_fix_timeline(timeline_data: dict, video_info: dict, script_tts_info: dict) -> dict:
    """타임라인 데이터의 유효성을 검사하고 필요시 보정합니다."""
    video_duration = video_info.get('duration', 0)
    
    # scenes 존재 여부 확인
    if 'scenes' not in timeline_data:
        timeline_data['scenes'] = []
    
    # 각 장면의 start_sec 유효성 검사
    for scene in timeline_data['scenes']:
        if 'source_video_timestamp' in scene:
            start_sec = scene['source_video_timestamp'].get('start_sec', 0)
            # 영상 길이를 초과하는 경우 보정
            if start_sec >= video_duration:
                scene['source_video_timestamp']['start_sec'] = max(0, video_duration - 5)
        
        # visual_padding_sec 기본값 설정
        if 'visual_padding_sec' not in scene:
            scene['visual_padding_sec'] = 0.5
    
    return timeline_data


def create_fallback_timeline(script_tts_info: dict, video_path: str, video_info: dict) -> dict:
    """API 호출 실패 시 기본 타임라인을 생성합니다."""
    video_duration = video_info.get('duration', 30)
    scene_audio_files = script_tts_info.get("scene_audio_files", [])
    
    scenes = []
    current_time = 0
    
    for i, scene_data in enumerate(scene_audio_files):
        # 영상 구간을 균등 분할
        start_sec = (i * video_duration / len(scene_audio_files)) if len(scene_audio_files) > 0 else 0
        start_sec = min(start_sec, video_duration - 1)
        
        scenes.append({
            "scene_id": scene_data.get("scene", i + 1),
            "description": f"장면 {i + 1}",
            "source_video_timestamp": {
                "start_sec": start_sec
            },
            "effects": [],
            "narration": scene_data.get("narration", ""),
            "text_overlay": {
                "text": f"장면 {i + 1}",
                "position": "bottom_center",
                "font_size": 35,
                "color": "white",
                "stroke_color": "black",
                "stroke_width": 2
            },
            "tts_audio_file": scene_data.get("audio_path", ""),
            "tts_duration_sec": scene_data.get("duration_sec", 0.0),
            "visual_padding_sec": 0.5
        })
    
    return {
        "video_source_file": video_path,
        "title": "교통사고 분석 - 자동 생성",
        "final_liability_ratio": {
            "car": 0,
            "bicycle": 100
        },
        "summary_narration": "교통사고 상황을 분석한 영상입니다.",
        "scenes": scenes,
        "outro": {
            "duration": 3.0,
            "background_color": [0, 0, 0],
            "text": "안전 운전하세요!",
            "narration": "안전 운전하세요."
        }
    } 