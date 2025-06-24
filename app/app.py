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

# .env에서 GOOGLE_API_KEY 읽기
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Set page config
st.set_page_config(page_title="사고 판단 챗봇", page_icon="⚖️")
st.title("⚖️ 한문철 스타일 사고 판단 챗봇")

# File uploader for video
uploaded_video = st.file_uploader("사고 동영상을 업로드하세요", type=['mp4', 'mov', 'avi'])

# Text input for additional information
text_input = st.text_area("추가 정보 입력", placeholder="사고 상황에 대한 추가 설명을 입력해 주세요.")

if uploaded_video is not None and st.button("사고 분석 및 모델 실행"):
    video_path = save_uploaded_video(uploaded_video)
    try:
        with st.spinner('사고 분석 및 모델 실행 중...'):
            if not text_input.strip():
                st.warning("추가 정보를 입력해 주세요. (예: 사고 상황 설명)")
            else:
                analyzer = AccidentVideoAnalyzer(api_key=api_key)
                result = analyzer.analyze(video_path, additional_info=text_input)
                st.subheader("분석 결과 (JSON)")
                st.json(result)
                # 분석 결과를 항상 jsons/tmp_result.json에 저장
                json_dir = os.path.join(os.path.dirname(__file__), '..', 'jsons')
                os.makedirs(json_dir, exist_ok=True)
                json_path = os.path.join(json_dir, 'tmp_result.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                # 분석이 성공했을 때만 모델 실행
                try:
                    model_result = run_rag_on_accident_json()
                    st.subheader('🧑‍💻 모델 최종 결과', anchor=False)
                    st.write(model_result)
                except Exception as e:
                    st.error(f"모델 실행 중 오류 발생: {e}")
    finally:
        cleanup_temp_file(video_path)

# Add some styling
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)












# import streamlit as st
# import os
# import time  # 스피너 효과를 보여주기 위한 임시 모듈
# import json  # 분석 결과를 시뮬레이션하기 위한 임시 모듈

# # 실제 사용 시 다음 유틸리티 함수들을 임포트해야 합니다.
# # from utils.file_handler import save_uploaded_video, cleanup_temp_file
# # from utils.accident_video_analyzer import AccidentVideoAnalyzer
# # from dotenv import load_dotenv

# # --- 환경 설정 (실제 환경에서는 .env 파일 사용) ---
# # load_dotenv()
# # api_key = os.getenv("GOOGLE_API_KEY")
# api_key = "DUMMY_API_KEY" # 데모용 임시 키

# # --- 페이지 기본 설정 ---
# st.set_page_config(
#     page_title="AI 교통사고 분석",
#     page_icon="⚖️",
#     layout="wide",
#     initial_sidebar_state="collapsed",
# )

# # --- 타이틀 및 설명 ---
# st.title("⚖️ AI가 분석하는 내 사고, 과실 비율은?")
# st.caption("한문철 변호사도 깜짝 놀랄 AI 분석. 영상과 상황을 입력하면 AI가 과실 비율을 예측해 드립니다.")
# st.divider()


# # --- 입력 섹션: 카드 UI와 2단 레이아웃 ---
# with st.container(border=True):
#     col1, col2 = st.columns(2)

#     with col1:
#         st.subheader("STEP 1. 사고 영상 업로드", help="mp4, mov, avi 형식의 파일을 올려주세요.")
#         uploaded_video = st.file_uploader(
#             "사고 동영상을 여기에 끌어다 놓거나 클릭해서 업로드하세요.",
#             type=['mp4', 'mov', 'avi'],
#             label_visibility="collapsed"
#         )
#         if uploaded_video:
#             st.video(uploaded_video)

#     with col2:
#         st.subheader("STEP 2. 추가 정보 입력", help="AI가 상황을 더 정확하게 이해할 수 있도록 사고 당시 상황을 구체적으로 작성해주세요.")
#         text_input = st.text_area(
#             "추가 정보 입력",
#             placeholder=(
#                 "예시)\n"
#                 "- 저는 직진 신호에 주행 중이었습니다.\n"
#                 "- 상대방 차량이 방향지시등 없이 갑자기 끼어들었습니다.\n"
#                 "- 도로는 편도 2차선이었고, 날씨는 맑았습니다."
#             ),
#             height=250,
#             label_visibility="collapsed"
#         )

# # --- 분석 시작 버튼 ---
# st.write("") # 여백
# analyze_button = st.button("🤖 AI로 분석 시작하기", type="primary", use_container_width=True, disabled=(not uploaded_video or not text_input))

# # --- 분석 로직 및 결과 표시 ---
# if analyze_button:
#     # # 실제 파일 처리 로직 (주석 처리)
#     # video_path = save_uploaded_video(uploaded_video)

#     try:
#         with st.spinner('AI가 사고 영상을 정밀 분석 중입니다. 잠시만 기다려주세요...'):
#             # # 실제 분석기 실행 로직 (주석 처리)
#             # analyzer = AccidentVideoAnalyzer(api_key=api_key)
#             # result = analyzer.analyze(video_path, additional_info=text_input)

#             # --- 데모용 가상 분석 결과 (2초 지연) ---
#             time.sleep(2)
#             # 실제 분석 결과(JSON)가 다음과 같은 형식이라고 가정
#             result = {
#                 "fault_ratio": {
#                     "my_car": 70,
#                     "other_car": 30
#                 },
#                 "summary": "블랙박스 차량은 정상 직진 중. 상대 차량이 방향지시등 없이 차선을 변경하여 발생한 사고로 분석됩니다. 도로교통법 제19조(안전거리 확보 등) 및 제38조(차의 신호) 위반 소지가 있습니다.",
#                 "legal_opinion": "상대 차량의 갑작스러운 차선 변경이 사고의 주된 원인으로 보입니다. 일반적으로 이러한 경우, 차선 변경 차량의 과실이 더 높게 산정됩니다. 보험사 및 법적 절차 진행 시 '안전운전 의무 불이행'을 강력하게 주장할 수 있습니다."
#             }
#             # ------------------------------------

#         st.divider()
#         st.subheader("📈 AI 분석 결과", anchor=False)

#         # --- 결과 요약: 카드 UI ---
#         with st.container(border=True):
#             ratio = result.get("fault_ratio", {})
#             my_fault = ratio.get("my_car", 50)
#             other_fault = ratio.get("other_car", 50)

#             # 과실 비율 시각화
#             st.write("#### 예상 과실 비율")
#             r_col1, r_col2 = st.columns(2)
#             with r_col1:
#                 st.metric(label="나 (블랙박스)", value=f"{my_fault} %")
#             with r_col2:
#                 st.metric(label="상대방", value=f"{other_fault} %")

#             # 프로그레스 바로 시각적 표현 추가
#             st.progress(my_fault / 100, text=f"과실 비율: 나 {my_fault}% : 상대방 {other_fault}%")

#             st.write("") # 여백

#             # 사고 내용 요약
#             st.write("#### 📝 사고 상황 요약")
#             st.info(result.get("summary", "요약 정보를 불러올 수 없습니다."))

#             st.write("") # 여백

#             # 법률적 소견 및 조언
#             st.write("#### 🧑‍⚖️ 법률적 소견 (AI 기반)")
#             st.success(result.get("legal_opinion", "법률적 소견을 불러올 수 없습니다."))

#         # 상세 데이터 (JSON)는 숨겨서 제공
#         with st.expander("전체 분석 데이터 보기 (Raw JSON)"):
#             st.json(result)

#     except Exception as e:
#         st.error(f"분석 중 오류가 발생했습니다: {e}")
#     # finally:
#         # # 임시 파일 정리 (실제 환경)
#         # cleanup_temp_file(video_path)
