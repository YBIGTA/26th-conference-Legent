import os
import io
import json
import shutil
from datetime import datetime
from typing import List, Dict

# Set up Google Cloud credentials automatically
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "legent-463917-0e7c6442775b.json")
if os.path.exists(CREDENTIALS_PATH):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
    print(f"🔑 [DEBUG] Using Google Cloud credentials: {CREDENTIALS_PATH}")
else:
    print(f"❌ [DEBUG] Google Cloud credentials not found at: {CREDENTIALS_PATH}")

try:
    from google.cloud import texttospeech
    from pydub import AudioSegment
    from mutagen.mp3 import MP3
    TTS_AVAILABLE = True
    print("✅ [DEBUG] Google Cloud TTS libraries loaded successfully")
except ImportError as e:
    TTS_AVAILABLE = False
    print(f"❌ [DEBUG] TTS libraries import failed: {e}")


def tts_generate_from_script(script_data: dict, output_dir: str = "tts_output") -> dict:
    """
    입력:
        - script_data: Phase 3에서 생성된 스크립트 데이터 (dict)
            {
                "scene_scripts": [
                    {"scene": 1, "visual": "...", "narration": "..."},
                    {"scene": 2, "visual": "...", "narration": "..."}
                ],
                "full_narration": "전체 내레이션"
            }
        - output_dir: TTS 파일들을 저장할 디렉토리 (str)
    출력:
        - TTS 결과 및 시간 정보
            {
                "scene_audio_files": [
                    {"scene": 1, "audio_path": "tts_output/scene01.mp3", "duration_sec": 10.5, "narration": "..."},
                    {"scene": 2, "audio_path": "tts_output/scene02.mp3", "duration_sec": 8.3, "narration": "..."}
                ],
                "total_duration": 18.8,
                "manifest_path": "tts_output/tts_manifest.json"
            }
    """
    if not TTS_AVAILABLE:
        return {
            "scene_audio_files": [],
            "total_duration": 0.0,
            "error": "TTS 라이브러리가 설치되지 않았습니다. pip install google-cloud-texttospeech pydub mutagen"
        }

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # Google Cloud TTS 클라이언트 초기화
    try:
        client = texttospeech.TextToSpeechClient()
    except Exception as e:
        return {
            "scene_audio_files": [],
            "total_duration": 0.0,
            "error": f"Google Cloud TTS 인증 실패: {e}. GOOGLE_APPLICATION_CREDENTIALS 환경변수를 확인하세요."
        }

    # TTS 설정
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name="ko-KR-Chirp3-HD-Algenib",  # 한문철 스타일에 맞는 음성
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
    )
    
    audio_cfg = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.25,  # 정상 속도
        pitch=0.0,  # 기본 피치
    )

    scene_audio_files = []
    total_duration = 0.0
    
    # ffprobe 사용 가능 여부 확인
    ffprobe_ok = shutil.which("ffprobe") is not None

    # 각 장면의 내레이션을 TTS로 변환
    for scene_data in script_data.get("scene_scripts", []):
        scene_num = scene_data.get("scene", 1)
        narration = scene_data.get("narration", "")
        
        if not narration.strip():
            continue
            
        try:
            # TTS 생성
            response = client.synthesize_speech(
                input=texttospeech.SynthesisInput(text=narration),
                voice=voice,
                audio_config=audio_cfg,
            )
            
            # 파일 저장
            filename = f"scene{scene_num:02d}_{datetime.now():%Y%m%d_%H%M%S}.mp3"
            file_path = os.path.join(output_dir, filename)
            
            with open(file_path, "wb") as f:
                f.write(response.audio_content)
            
            # 오디오 길이 측정
            try:
                if ffprobe_ok:
                    duration = AudioSegment.from_file(file_path).duration_seconds
                else:
                    duration = MP3(file_path).info.length
                duration = round(duration, 3)
            except Exception:
                # 길이 측정 실패 시 기본값 (텍스트 길이 기반 추정)
                duration = len(narration) * 0.1  # 대략적인 추정
            
            scene_audio_files.append({
                "scene": scene_num,
                "audio_path": file_path,
                "duration_sec": duration,
                "narration": narration,
                "visual": scene_data.get("visual", "")
            })
            
            total_duration += duration
            
            print(f"[Scene {scene_num}] {filename} → {duration}s")
            
        except Exception as e:
            print(f"Scene {scene_num} TTS 생성 실패: {e}")
            # 실패한 장면도 기록 (0초 길이로)
            scene_audio_files.append({
                "scene": scene_num,
                "audio_path": "",
                "duration_sec": 0.0,
                "narration": narration,
                "visual": scene_data.get("visual", ""),
                "error": str(e)
            })

    # 매니페스트 파일 저장
    manifest_data = {
        "scene_audio_files": scene_audio_files,
        "total_duration": round(total_duration, 3),
        "generated_at": datetime.now().isoformat(),
        "original_script": script_data
    }
    
    manifest_path = os.path.join(output_dir, "tts_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ TTS 생성 완료. 총 {len(scene_audio_files)}개 장면, {total_duration}초")
    print(f"✅ 매니페스트 저장: {manifest_path}")
    
    return {
        "scene_audio_files": scene_audio_files,
        "total_duration": round(total_duration, 3),
        "manifest_path": manifest_path
    }


def tts_generate(narration_text: str) -> dict:
    """
    단일 내레이션 텍스트를 TTS로 변환하는 기존 함수 (하위 호환성)
    입력:
        - narration_text: 내레이션 텍스트 (str)
    출력:
        - 오디오 파일 경로 및 재생 시간 예시
            {
                "audio_path": "audio/scene1.wav",
                "duration_sec": 10.5
            }
    """
    # 단일 텍스트를 스크립트 형식으로 변환
    script_data = {
        "scene_scripts": [
            {"scene": 1, "narration": narration_text, "visual": ""}
        ],
        "full_narration": narration_text
    }
    
    result = tts_generate_from_script(script_data)
    
    if result.get("scene_audio_files") and len(result["scene_audio_files"]) > 0:
        first_scene = result["scene_audio_files"][0]
        return {
            "audio_path": first_scene.get("audio_path", ""),
            "duration_sec": first_scene.get("duration_sec", 0.0)
        }
    else:
        return {
            "audio_path": "",
            "duration_sec": 0.0,
            "error": result.get("error", "TTS 생성 실패")
        } 