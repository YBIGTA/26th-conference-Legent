import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import shutil
import logging
import traceback
from tqdm import tqdm

try:
    from moviepy import *
    from moviepy import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


def render_final_video(timeline_json: dict, video_path: str, output_dir: str = "output") -> str:
    """
    입력:
        - timeline_json: Phase 5에서 생성된 최종 타임라인 JSON (dict)
        - video_path: 원본 영상 경로 (str)
        - output_dir: 출력 디렉토리 (str)
    출력:
        - result_video_path: 최종 영상 파일 경로 (str)
    """
    print("🎬 [DEBUG] Starting render_final_video function")
    print(f"🎬 [DEBUG] Input parameters:")
    print(f"   - video_path: {video_path}")
    print(f"   - output_dir: {output_dir}")
    print(f"   - timeline_json keys: {list(timeline_json.keys()) if timeline_json else 'None'}")
    
    if not MOVIEPY_AVAILABLE:
        error_msg = "ERROR: MoviePy가 설치되지 않았습니다. pip install moviepy"
        print(f"❌ [DEBUG] {error_msg}")
        return error_msg
    
    if not os.path.exists(video_path):
        error_msg = f"ERROR: 원본 영상 파일을 찾을 수 없습니다: {video_path}"
        print(f"❌ [DEBUG] {error_msg}")
        return error_msg
    
    # 출력 디렉토리 생성
    print(f"🎬 [DEBUG] Creating output directory: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    print(f"✅ [DEBUG] Output directory created/exists")
    
    try:
        # 원본 영상 로드
        print(f"🎬 [DEBUG] Loading original video: {video_path}")
        original_video = VideoFileClip(video_path)
        print(f"✅ [DEBUG] 원본 영상 로드 완료: {video_path}")
        print(f"   - Duration: {original_video.duration}초")
        print(f"   - FPS: {original_video.fps}")
        print(f"   - Size: {original_video.size}")
        
        # 장면별 클립 생성
        print(f"🎬 [DEBUG] Creating scene clips")
        scene_clips = []
        scenes = timeline_json.get("scenes", [])
        print(f"🎬 [DEBUG] Found {len(scenes)} scenes to process")
        
        for i, scene in enumerate(tqdm(scenes, desc="장면 처리 중"), 1):
            print(f"🎬 [DEBUG] Processing scene {i}/{len(scenes)}")
            try:
                scene_clip = create_scene_clip(scene, original_video)
                if scene_clip:
                    scene_clips.append(scene_clip)
                    print(f"✅ [DEBUG] Scene {i} clip created successfully")
                else:
                    print(f"❌ [DEBUG] Scene {i} clip creation failed")
            except Exception as e:
                print(f"❌ [DEBUG] Exception in scene {i}: {e}")
                print(f"❌ [DEBUG] Scene {i} traceback: {traceback.format_exc()}")
        
        if not scene_clips:
            error_msg = "ERROR: 생성된 장면 클립이 없습니다."
            print(f"❌ [DEBUG] {error_msg}")
            return error_msg
        
        print(f"✅ [DEBUG] Successfully created {len(scene_clips)} scene clips")
        
        # 최종 영상 합성
        print(f"🎬 [DEBUG] Concatenating {len(scene_clips)} scene clips")
        try:
            final_video = concatenate_videoclips(scene_clips, method="compose")
            print(f"✅ [DEBUG] Scene concatenation successful")
        except Exception as e:
            print(f"❌ [DEBUG] Scene concatenation failed: {e}")
            print(f"❌ [DEBUG] Concatenation traceback: {traceback.format_exc()}")
            raise
        
        # 아웃트로 추가
        print(f"🎬 [DEBUG] Creating outro clip")
        try:
            outro_clip = create_outro_clip(timeline_json.get("outro", {}))
            if outro_clip:
                print(f"✅ [DEBUG] Outro clip created, adding to final video")
                final_video = concatenate_videoclips([final_video, outro_clip], method="compose")
                print(f"✅ [DEBUG] Outro added to final video")
            else:
                print(f"ℹ️ [DEBUG] No outro clip created")
        except Exception as e:
            print(f"❌ [DEBUG] Outro creation/addition failed: {e}")
            print(f"❌ [DEBUG] Outro traceback: {traceback.format_exc()}")
            # Continue without outro
        
        # 출력 파일 경로
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"final_video_{timestamp}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        print(f"🎬 [DEBUG] Output path: {output_path}")
        
        # 최종 영상 렌더링
        print(f"🎥 [DEBUG] Starting final video rendering to: {output_path}")
        try:
            final_video.write_videofile(
                output_path,
                fps=30,
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
            )
            print(f"✅ [DEBUG] Video rendering completed successfully")
        except Exception as e:
            print(f"❌ [DEBUG] Video rendering failed: {e}")
            print(f"❌ [DEBUG] Rendering traceback: {traceback.format_exc()}")
            raise
        
        # 리소스 정리
        print(f"🎬 [DEBUG] Cleaning up resources")
        try:
            original_video.close()
            final_video.close()
            for i, clip in enumerate(scene_clips):
                clip.close()
            if 'outro_clip' in locals() and outro_clip:
                outro_clip.close()
            print(f"✅ [DEBUG] Resource cleanup completed")
        except Exception as e:
            print(f"⚠️ [DEBUG] Resource cleanup warning: {e}")
        
        print(f"✅ [DEBUG] 최종 영상 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ [DEBUG] 영상 렌더링 실패: {e}")
        print(f"❌ [DEBUG] Full traceback: {traceback.format_exc()}")
        return f"ERROR: {e}"


def create_scene_clip(scene: dict, original_video: VideoFileClip) -> Optional[VideoFileClip]:
    """개별 장면 클립을 생성합니다."""
    try:
        scene_id = scene.get("scene_id", 1)
        print(f"🎥 [DEBUG] [Scene {scene_id}] Starting scene clip creation")
        print(f"🎥 [DEBUG] [Scene {scene_id}] Scene data keys: {list(scene.keys())}")
        
        # 비디오 구간 추출
        timestamp = scene.get("source_video_timestamp", {})
        start_sec = timestamp.get("start_sec", 0.0)
        tts_duration = scene.get("tts_duration_sec", 5.0)
        visual_padding = scene.get("visual_padding_sec", 0.5)
        
        # 총 클립 길이 = TTS 길이 + 패딩
        total_duration = tts_duration + visual_padding
        
        # 원본 영상에서 해당 구간 추출
        end_sec = min(start_sec + total_duration, original_video.duration)
        if start_sec >= original_video.duration:
            start_sec = max(0, original_video.duration - total_duration)
        
        print(f"🎥 [DEBUG] [Scene {scene_id}] Extracting video subclip: {start_sec}s - {end_sec}s")
        try:
            video_clip = original_video.subclipped(start_sec, end_sec)
            print(f"✅ [DEBUG] [Scene {scene_id}] Video subclip extracted (duration: {video_clip.duration}s)")
        except Exception as e:
            print(f"❌ [DEBUG] [Scene {scene_id}] Video subclip failed: {e}")
            raise
        
        # 클립 길이가 필요한 길이보다 짧으면 반복 또는 정지
        print(f"🎥 [DEBUG] [Scene {scene_id}] Duration check - current: {video_clip.duration}s, needed: {total_duration}s")
        if video_clip.duration < total_duration:
            print(f"🎥 [DEBUG] [Scene {scene_id}] Video too short, adding padding")
            try:
                # 마지막 프레임으로 정지 영상 생성
                last_frame = video_clip.to_ImageClip(t=video_clip.duration-0.1)
                padding_clip = last_frame.with_duration(total_duration - video_clip.duration)
                video_clip = concatenate_videoclips([video_clip, padding_clip])
                print(f"✅ [DEBUG] [Scene {scene_id}] Padding added successfully")
            except Exception as e:
                print(f"❌ [DEBUG] [Scene {scene_id}] Padding failed: {e}")
                raise
        elif video_clip.duration > total_duration:
            print(f"🎥 [DEBUG] [Scene {scene_id}] Video too long, trimming")
            try:
                # 필요한 길이만큼만 자르기
                video_clip = video_clip.subclipped(0, total_duration)
                print(f"✅ [DEBUG] [Scene {scene_id}] Video trimmed successfully")
            except Exception as e:
                print(f"❌ [DEBUG] [Scene {scene_id}] Video trimming failed: {e}")
                raise
        
        # TTS 오디오 추가
        tts_audio_file = scene.get("tts_audio_file", "")
        print(f"🎥 [DEBUG] [Scene {scene_id}] TTS audio file: {tts_audio_file}")
        if tts_audio_file and os.path.exists(tts_audio_file):
            print(f"🎥 [DEBUG] [Scene {scene_id}] Adding TTS audio...")
            try:
                audio_clip = AudioFileClip(tts_audio_file)
                # 오디오 길이에 맞춰 조정
                if audio_clip.duration < total_duration:
                    # 오디오가 짧으면 뒤에 무음 추가
                    from moviepy.audio.AudioClip import AudioArrayClip
                    import numpy as np
                    silence_duration = total_duration - audio_clip.duration
                    silence_array = np.zeros((int(silence_duration * 44100), 2))  # 44.1kHz stereo
                    silence = AudioArrayClip(silence_array, fps=44100)
                    audio_clip = concatenate_audioclips([audio_clip, silence])
                else:
                    # 오디오가 길면 자르기
                    audio_clip = audio_clip.subclipped(0, total_duration)
                
                video_clip = video_clip.with_audio(audio_clip)
                print(f"✅ [DEBUG] [Scene {scene_id}] TTS 오디오 추가 완료")
            except Exception as e:
                print(f"❌ [DEBUG] [Scene {scene_id}] TTS 오디오 추가 실패: {e}")
                print(f"❌ [DEBUG] [Scene {scene_id}] TTS traceback: {traceback.format_exc()}")
        else:
            print(f"ℹ️ [DEBUG] [Scene {scene_id}] No TTS audio file or file doesn't exist")
        
        # 텍스트 오버레이 추가
        text_overlay = scene.get("text_overlay", {})
        print(f"🎥 [DEBUG] [Scene {scene_id}] Text overlay: {text_overlay.get('text', 'None')}")
        if text_overlay.get("text"):
            print(f"🎥 [DEBUG] [Scene {scene_id}] Adding text overlay...")
            try:
                video_clip = add_text_overlay(video_clip, text_overlay)
                print(f"✅ [DEBUG] [Scene {scene_id}] Text overlay added successfully")
            except Exception as e:
                print(f"❌ [DEBUG] [Scene {scene_id}] Text overlay failed: {e}")
                print(f"❌ [DEBUG] [Scene {scene_id}] Text overlay traceback: {traceback.format_exc()}")
                # Continue without text overlay
        else:
            print(f"ℹ️ [DEBUG] [Scene {scene_id}] No text overlay")
        
        print(f"✅ [DEBUG] [Scene {scene_id}] 클립 생성 완료 (길이: {video_clip.duration}초)")
        return video_clip
        
    except Exception as e:
        scene_id = scene.get('scene_id', '?')
        print(f"❌ [DEBUG] [Scene {scene_id}] 클립 생성 실패: {e}")
        print(f"❌ [DEBUG] [Scene {scene_id}] Full traceback: {traceback.format_exc()}")
        return None


def add_text_overlay(video_clip: VideoFileClip, text_config: dict) -> VideoFileClip:
    """비디오 클립에 텍스트 오버레이를 추가합니다."""
    print(f"🎨 [DEBUG] Starting text overlay addition")
    try:
        text = text_config.get("text", "")
        print(f"🎨 [DEBUG] Text overlay config: {text_config}")
        if not text:
            print(f"ℹ️ [DEBUG] No text provided, returning original clip")
            return video_clip
        
        # 텍스트 설정
        fontsize = text_config.get("font_size", 35)
        color = text_config.get("color", "white")
        stroke_color = text_config.get("stroke_color", "black")
        stroke_width = text_config.get("stroke_width", 2)
        position = text_config.get("position", "bottom_center")
        
        # 위치 설정 매핑
        position_map = {
            "center": ("center", "center"),
            "bottom_center": ("center", 0.8),
            "top_center": ("center", 0.1),
            "top_left": (0.1, 0.1),
            "top_right": (0.9, 0.1),
            "bottom_left": (0.1, 0.9),
            "bottom_right": (0.9, 0.9)
        }
        
        pos = position_map.get(position, ("center", 0.8))
        
        # 텍스트 클립 생성
        print(f"🎨 [DEBUG] Creating TextClip with font_size={fontsize}, color={color}")
        try:
            text_clip = TextClip(
                text=text,
                font_size=fontsize,
                color=color,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                font='NanumGothic',
                method='caption',
                size=(int(video_clip.w * 0.8), None)  # 텍스트 폭 제한
            ).with_duration(video_clip.duration).with_position(pos)
            print(f"✅ [DEBUG] TextClip created successfully")
        except Exception as e:
            print(f"❌ [DEBUG] TextClip creation failed: {e}")
            print(f"❌ [DEBUG] TextClip traceback: {traceback.format_exc()}")
            raise
        
        # 비디오와 텍스트 합성
        print(f"🎨 [DEBUG] Compositing video and text")
        try:
            result = CompositeVideoClip([video_clip, text_clip])
            print(f"✅ [DEBUG] Text overlay composition successful")
            return result
        except Exception as e:
            print(f"❌ [DEBUG] Text overlay composition failed: {e}")
            print(f"❌ [DEBUG] Composition traceback: {traceback.format_exc()}")
            raise
        
    except Exception as e:
        print(f"❌ [DEBUG] 텍스트 오버레이 추가 실패: {e}")
        print(f"❌ [DEBUG] Text overlay full traceback: {traceback.format_exc()}")
        return video_clip


def create_outro_clip(outro_config: dict) -> Optional[VideoFileClip]:
    """아웃트로 클립을 생성합니다."""
    print(f"🎥 [DEBUG] Starting outro clip creation")
    if not outro_config:
        print(f"ℹ️ [DEBUG] No outro config provided")
        return None
    
    print(f"🎥 [DEBUG] Outro config: {outro_config}")
    try:
        duration = outro_config.get("duration", 3.0)
        bg_color = outro_config.get("background_color", [0, 0, 0])
        text = outro_config.get("text", "안전 운전하세요!")
        
        # 배경 생성
        print(f"🎥 [DEBUG] Creating background clip: {bg_color}, duration={duration}s")
        bg_clip = ColorClip(size=(1920, 1080), color=bg_color, duration=duration)
        print(f"✅ [DEBUG] Background clip created")
        
        # 텍스트 클립 생성
        print(f"🎥 [DEBUG] Creating outro text clip: '{text}'")
        try:
            text_clip = TextClip(
                text=text,
                font_size=60,
                color='white',
                stroke_color='black',
                stroke_width=3,
                font='NanumGothic',
                method='caption',
                size=(1920, None)
            ).with_duration(duration).with_position('center')
            print(f"✅ [DEBUG] Outro text clip created")
        except Exception as e:
            print(f"❌ [DEBUG] Outro text clip failed: {e}")
            print(f"❌ [DEBUG] Outro text traceback: {traceback.format_exc()}")
            raise
        
        # 합성
        print(f"🎥 [DEBUG] Compositing outro background and text")
        try:
            outro_clip = CompositeVideoClip([bg_clip, text_clip])
            print(f"✅ [DEBUG] Outro composition successful")
        except Exception as e:
            print(f"❌ [DEBUG] Outro composition failed: {e}")
            print(f"❌ [DEBUG] Outro composition traceback: {traceback.format_exc()}")
            raise
        
        print(f"✅ [DEBUG] 아웃트로 생성 완료 (길이: {duration}초)")
        return outro_clip
        
    except Exception as e:
        print(f"❌ [DEBUG] 아웃트로 생성 실패: {e}")
        print(f"❌ [DEBUG] Outro full traceback: {traceback.format_exc()}")
        return None


def render_simple_video_from_tts(tts_results: List[Dict], output_path: str = "simple_video.mp4") -> str:
    """
    TTS 결과만으로 간단한 영상을 생성합니다 (테스트용)
    입력:
        - tts_results: TTS 결과 리스트 [{"text": "...", "file_path": "...", "duration_seconds": 3.2}, ...]
        - output_path: 출력 파일 경로
    """
    if not MOVIEPY_AVAILABLE:
        return f"ERROR: MoviePy가 설치되지 않았습니다."
    
    try:
        clips = []
        
        for idx, result in enumerate(tts_results, 1):
            text = result.get("text", f"장면 {idx}")
            duration = result.get("duration_seconds", 3.0)
            audio_path = result.get("file_path", "")
            
            # 배경 생성
            bg = ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=duration)
            
            # 텍스트 클립
            text_clip = TextClip(
                text=text,
                font_size=40,
                color='white',
                stroke_color='black',
                stroke_width=2,
                font='NanumGothic',
                method='caption',
                size=(1600, None)
            ).with_duration(duration).with_position('center')
            
            # 비디오 합성
            video_clip = CompositeVideoClip([bg, text_clip])
            
            # 오디오 추가
            if audio_path and os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                video_clip = video_clip.with_audio(audio_clip)
            
            clips.append(video_clip)
        
        # 최종 합성
        final_video = concatenate_videoclips(clips, method="compose")
        final_video.write_videofile(output_path, fps=30)
        
        # 리소스 정리
        final_video.close()
        for clip in clips:
            clip.close()
        
        print(f"✅ 간단한 영상 생성 완료: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ 간단한 영상 생성 실패: {e}")
        return f"ERROR: {e}" 