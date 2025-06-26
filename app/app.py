import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from utils.file_handler import save_uploaded_video, cleanup_temp_file
from utils.accident_video_analyzer import AccidentVideoAnalyzer
from dotenv import load_dotenv
import json
import datetime
from models.script_query import run_rag_on_accident_json

# Import video pipeline phases
from models.video.phase2A_timestamp import extract_timestamps_json
from models.video.phase3_script import generate_creative_script
from models.video.phase4_tts import tts_generate_from_script
from models.video.phase5_timeline import create_final_timeline
from models.video.phase6_render import render_final_video

# .env에서 GOOGLE_API_KEY 읽기
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Set page config
st.set_page_config(page_title="AI 교통사고 분석 & 영상 제작", page_icon="⚖️", layout="wide")
st.title("⚖️ 한문철TV 스타일 AI 교통사고 분석 & 자동 영상 제작")

# Sidebar for options
st.sidebar.title("🎬 기능 선택")
mode = st.sidebar.radio(
    "원하는 기능을 선택하세요:",
    ["📊 사고 분석만", "🎥 영상 제작까지"]
)

# File uploader for video
uploaded_video = st.file_uploader("사고 동영상을 업로드하세요", type=['mp4', 'mov', 'avi'])

# Text input for additional information
text_input = st.text_area("추가 정보 입력", placeholder="사고 상황에 대한 추가 설명을 입력해 주세요.")

def run_video_pipeline(video_path: str, analysis_result: dict) -> str:
    """Complete video pipeline execution"""
    try:
        st.write("🎬 **Phase 2A: 타임스탬프 추출 중...**")
        timestamps = extract_timestamps_json(video_path, analysis_result)
        st.success("✅ 타임스탬프 추출 완료")
        
        # Show timestamps output
        with st.expander("📋 Phase 2A 결과 보기"):
            st.json(timestamps)
        
        st.write("🎭 **Phase 3: 한문철 스타일 스크립트 생성 중...**")
        script_data = generate_creative_script(analysis_result, timestamps)
        st.success("✅ 창의적 스크립트 생성 완료")
        
        # Show script output
        with st.expander("📝 Phase 3 결과 보기"):
            st.json(script_data)
        
        st.write("🔊 **Phase 4: TTS 음성 생성 중...**")
        tts_data = tts_generate_from_script(script_data)
        st.success(f"✅ TTS 생성 완료 (총 {tts_data.get('total_duration', 0)}초)")
        
        # Show TTS output
        with st.expander("🔊 Phase 4 결과 보기"):
            st.json(tts_data)
        
        st.write("⏰ **Phase 5: 최종 타임라인 생성 중...**")
        timeline_json = create_final_timeline(tts_data, video_path)
        st.success("✅ 타임라인 생성 완료")
        
        # Show timeline output with special attention to scenes
        with st.expander("⏰ Phase 5 결과 보기 (타임라인)"):
            st.json(timeline_json)
            if 'scenes' in timeline_json:
                st.info(f"🎬 생성된 장면 수: {len(timeline_json['scenes'])}")
                for i, scene in enumerate(timeline_json['scenes'][:3]):  # Show first 3 scenes
                    st.write(f"**Scene {i+1}:** {scene.get('description', 'No description')}")
            else:
                st.error("❌ 타임라인에 'scenes' 키가 없습니다!")
        
        st.write("🎥 **Phase 6: 최종 영상 렌더링 중...**")
        
        final_video_path = render_final_video(timeline_json, video_path)
        
        if final_video_path and not final_video_path.startswith("ERROR"):
            st.success("✅ 한문철TV 스타일 영상 제작 완료!")
            return final_video_path
        else:
            st.error(f"영상 제작 실패: {final_video_path}")
            return None
            
    except Exception as e:
        st.error(f"영상 파이프라인 실행 중 오류: {e}")
        return None


if uploaded_video is not None and st.button(f"{'🎥 영상 제작 시작' if mode == '🎥 영상 제작까지' else '📊 사고 분석 시작'}"):
    video_path = save_uploaded_video(uploaded_video)
    try:
        if not text_input.strip():
            st.warning("추가 정보를 입력해 주세요. (예: 사고 상황 설명)")
        else:
            # Phase 1: Initial Analysis
            with st.spinner('🔍 Phase 1: 사고 분석 및 초기 데이터 생성 중...'):
                analyzer = AccidentVideoAnalyzer(api_key=api_key)
                result = analyzer.analyze(video_path, additional_info=text_input)

                # Save analysis result
                json_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'jsons')
                os.makedirs(json_dir, exist_ok=True)
                json_path = os.path.join(json_dir, 'tmp_result.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

            # Display analysis results
            st.subheader("📊 1차 분석 결과")
            with st.expander("분석 결과 보기"):
                st.json(result)

            # Phase 2: RAG Enhancement
            try:
                with st.spinner('🧠 Phase 2: RAG 기반 심화 분석 중...'):
                    rag_result = run_rag_on_accident_json()
                
                st.subheader('🧑‍💻 RAG 최종 보고서')
                st.write(rag_result)
                
                # If user selected video creation mode
                if mode == "🎥 영상 제작까지":
                    st.divider()
                    st.subheader("🎬 한문철TV 스타일 영상 자동 제작")
                    
                    with st.spinner('🎥 영상 제작 파이프라인 실행 중... (약 2-5분 소요)'):
                        final_video_path = run_video_pipeline(video_path, result)
                        
                        if final_video_path:
                            st.balloons()
                            st.success("🎉 한문철TV 스타일 영상이 완성되었습니다!")
                            
                            # Display video download link
                            if os.path.exists(final_video_path):
                                with open(final_video_path, "rb") as file:
                                    st.download_button(
                                        label="📥 완성된 영상 다운로드",
                                        data=file.read(),
                                        file_name=f"hanmuncheol_style_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                        mime="video/mp4"
                                    )
                                
                                # Display video preview
                                with st.expander("🎬 영상 미리보기"):
                                    st.video(final_video_path)
                            else:
                                st.error("영상 파일을 찾을 수 없습니다.")
                        
            except Exception as e:
                st.error(f"RAG 모델 실행 중 오류 발생: {e}")
                    
    finally:
        cleanup_temp_file(video_path)

# Add additional information section
st.divider()
with st.expander("ℹ️ 사용 가이드"):
    st.markdown("""
    ### 📊 사고 분석만 모드
    - 사고 영상을 분석하여 과실 비율과 법적 소견을 제공합니다
    - RAG 기술로 최신 판례와 법규를 반영한 상세 분석을 수행합니다
    
    ### 🎥 영상 제작까지 모드  
    - 사고 분석 + 한문철TV 스타일의 자동 영상 제작
    - AI가 한문철 변호사 스타일로 스크립트를 작성합니다
    - TTS 음성 생성 및 영상 편집까지 자동으로 처리됩니다
    - 완성된 영상을 다운로드할 수 있습니다
    
    ### 🔧 필요한 설정
    - Google Cloud TTS API 인증 (영상 제작 모드)
    - Gemini API 키 (GOOGLE_API_KEY 환경변수)
    - MoviePy 라이브러리 (영상 렌더링)
    """)

# Add some styling
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .stRadio > div {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)
