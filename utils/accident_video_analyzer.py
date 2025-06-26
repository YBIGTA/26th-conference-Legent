import google.generativeai as genai
import json
import time
import argparse
import os
from dotenv import load_dotenv

class AccidentVideoAnalyzer:
    """
    교통사고 영상을 분석하여 구조화된 JSON 텍스트로 변환하는 클래스.
    Gemini 2.5 Pro 모델을 사용하여 영상의 핵심 정보를 추출합니다.
    """

    def __init__(self, api_key: str):
        """
        AI 분석기를 초기화하고 Google Gemini API를 설정합니다.

        Args:
            api_key (str): Google AI Studio에서 발급받은 API 키.
        """
        if not api_key:
            raise ValueError("API 키가 제공되지 않았습니다. GOOGLE_API_KEY 환경 변수를 설정하거나 인자로 전달해야 합니다.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        print("AccidentVideoAnalyzer가 성공적으로 초기화되었습니다.")

    def _get_analysis_prompt(self) -> str:
        """
        Gemini 모델에 영상 분석을 요청하기 위한 고도화된 프롬프트를 생성합니다.
        Chain-of-Thought 워크플로우를 적용하여 분석의 정확성과 일관성을 극대화합니다.
        """
        prompt = """
        ## PERSONA
        당신은 대한민국 손해보험협회 소속의 최고 수준 교통사고 영상 분석 전문가입니다. 당신의 임무는 법률적, 물리적 사실에 기반하여 교통사고 영상을 객관적으로 분석하고, 과실 비율 산정의 기초가 되는 상세 데이터를 추출하는 것입니다.

        ## CORE_PRINCIPLES (핵심 분석 원칙)
        1.  **객관성 유지:** 어떠한 주관적 판단이나 편견 없이 영상에 나타난 시각적, 청각적 정보만을 기반으로 분석합니다. 'A차량이 잘못한 것 같다'와 같은 평가는 절대 포함하지 마십시오.
        2.  **근거 기반 분석:** 모든 분석 결과, 특히 법규 위반 사항에 대해서는 영상 속 근거를 명확히 제시해야 합니다. (예: '과속(추정)'의 근거로 '제한속도 40km/h 표지판이 있으나, 주변 차량보다 월등히 빠른 속도로 주행함'과 같이 서술)
        3.  **정확한 용어 사용:** 대한민국의 '도로교통법'과 '자동차사고 과실비율 인정기준'에 사용되는 표준 용어를 사용하여 각 상황을 기술합니다.
        4.  **불확실성 명시:** 영상만으로 판독이 불가능하거나 명확하지 않은 정보는 반드시 "확인 불가" 또는 "불분명"으로 명시합니다.

        ## ANALYSIS_WORKFLOW (사고 분석 워크플로우)
        먼저 아래 2가지 단계를 마음속으로 또는 스크래치패드에 체계적으로 수행하여 사고의 전체적인 맥락을 파악한 후, 그 결과를 종합하여 최종 OUTPUT_FORMAT(JSON)을 작성하십시오.

        ### [Step 1] Scene & Entities Identification (상황 및 개체 식별)
        -   **사고 장소 특정:** 영상의 배경이 되는 도로의 종류, 구조, 교통 시설물 등을 종합하여 사고 장소를 명확히 정의합니다. (예: 신호등이 없는 편도 1차선 이면도로의 T자형 삼거리)
        -   **개체 식별 및 정의:**
            -   **party_1:** 영상 촬영의 주체인 '블랙박스 차량'.
            -   **party_2, party_3...:** 사고에 관련된 다른 모든 차량, 이륜차, 자전거, 보행자 등을 순서대로 명명합니다.
            -   **보행자 특례:** 차량에서 하차했거나, 하차 중이거나, 차량 바로 옆에 서 있는 사람은 차량과 별개의 독립된 '보행자' 개체로 반드시 정의합니다.

        ### [Step 2] Chronological Event Reconstruction (시간 순서별 사건 재구성)
        -   **충돌 전 (Pre-Collision):** 충돌이 발생하기 직전, 각 개체(party_1, party_2 등)의 위치, 차로, 진행 방향, 속도, 특이 행동(방향지시등 점등, 급정지, 차선 변경 시도 등)을 시간 순으로 서술합니다.
        -   **충돌 시점 (At-Collision):** 어느 개체의 어느 부위가 다른 개체의 어느 부위와 최초로 접촉했는지 구체적으로 명시합니다. 충돌 시의 동적인 상황을 상세히 묘사합니다.
        -   **충돌 후 (Post-Collision):** 충돌 이후 각 개체의 움직임과 최종 정지 위치를 서술합니다.

        ## OUTPUT_FORMAT (JSON)
        위 분석 워크플로우를 통해 도출된 최종 결과를 다음 JSON 형식에 맞춰 **오직 JSON 코드 블록만** 출력하십시오.
        ```json
        {
        "accident_summary": "한 문장으로 요약된 사고 개요 (예: 신호 없는 교차로에서 좌회전하던 party_1 차량과 우측 도로에서 직진하던 party_2 차량이 충돌함)",
        "road_and_environment": {
            "road_type": "일반도로, 고속도로/자동차전용도로, 이면도로, 주차장, 기타 중 선택",
            "intersection_type": "사거리, 삼거리(T자형), 회전교차로, 교차로 아님, 기타 중 선택",
            "road_hierarchy": "대로/소로 구분 명확, 동일 폭, 확인 불가",
            "traffic_control": {
            "traffic_light_presence": "있음, 없음, 점멸신호",
            "traffic_signs": "영상에서 식별된 모든 표지판을 기재 (예: ['일시정지', '속도제한(30km/h)', '어린이보호구역'])",
            "road_markings": "영상에서 식별된 모든 노면표시를 기재 (예: ['중앙선(황색 실선)', '횡단보도', '좌회전 유도선'])"
            },
            "conditions": {
            "weather": "맑음, 흐림, 비, 눈",
            "time_of_day": "주간, 야간"
            }
        },
        "parties": [
            {
            "party_id": "party_1 (블랙박스 차량)",
            "type": "자동차, 이륜차, 자전거, 보행자, 기타",
            "maneuver": "직진, 좌회전, 우회전, 유턴, 차로변경, 후진, 주정차, 기타",
            "maneuver_detail": "구체적인 행위 서술 (예: '2차로에서 1차로로 진로 변경 중', '갓길에 정차 후 문을 여는 중')",
            "lane": "1차로, 2차로, 갓길, 안전지대, 차선 없음, 확인 불가",
            "signal_status": "행위 시작 시점의 신호 상태 (예: 녹색, 황색, 적색, 신호없음, 확인 불가)",
            "violations": [
                {
                "violation_type": "신호위반, 중앙선침범, 과속(추정), 지시위반(좌회전 차로에서 직진), 안전운전의무 불이행, 해당 없음",
                "evidence": "위반 사항에 대한 영상 속 근거 (예: '적색 신호에 교차로 진입함', '황색 중앙선을 넘어 추월 시도함')"
                }
            ]
            },
            {
            "party_id": "party_2",
            "type": "자동차, 이륜차, 자전거, 보행자, 기타",
            "maneuver": "직진, 좌회전, 우회전, 유턴, 차로변경, 후진, 주정차, 무단횡단, 기타",
            "maneuver_detail": "구체적인 행위 서술 (예: '맞은편 1차로에서 비보호 좌회전 시도')",
            "lane": "1차로, 2차로, 갓길, 횡단보도, 확인 불가",
            "signal_status": "행위 시작 시점의 신호 상태 (예: 녹색, 황색, 적색, 신호없음, 확인 불가)",
            "violations": [
                {
                "violation_type": "해당 없음",
                "evidence": ""
                }
            ]
            }
        ],
        "collision_dynamics": {
            "entry_order": "party_1 선진입, party_2 선진입, 동시 진입, 확인 불가",
            "point_of_impact_party_1": "party_1의 충돌 부위 (예: 전면 범퍼 중앙, 조수석 앞 휀더, 운전석 문)",
            "point_of_impact_party_2": "party_2의 충돌 부위 (예: 전면, 운전석 측면 중앙, 후면 범퍼)",
            "chronological_description": "사건 재구성 내용을 바탕으로 충돌 전-중-후 상황을 객관적으로 서술. (예: party_1이 2차로를 주행하던 중, party_2가 갓길에 정차했다가 방향지시등 없이 갑자기 2차로로 진입을 시작함. party_1이 이를 발견하고 제동했으나 피하지 못하고 party_1의 전면으로 party_2의 운전석 문 부분을 충돌함.)"
        }
        }
        ```
        """
        return prompt

    def get_prompt(self, accident_desc, additional_info=None):
        prompt = f"# 사고 상황 설명\n{accident_desc}\n"
        if additional_info:
            prompt += f"# 추가 정보\n{additional_info}\n"
        prompt += self._get_analysis_prompt()
        return prompt

    def analyze(self, video_path, accident_desc=None, additional_info=None):
        # 1. 파일 경로 체크
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"오류: 영상 파일을 찾을 수 없습니다. 경로: {video_path}")

        # 2. 프롬프트 생성
        prompt = self.get_prompt(accident_desc, additional_info)
        print(f"[{time.ctime()}] 영상 파일 업로드를 시작합니다: {video_path}")

        video_file = genai.upload_file(path=video_path)

        # 파일이 처리될 때까지 대기
        while video_file.state.name == "PROCESSING":
            print("..", end="", flush=True)
            time.sleep(5)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            raise ValueError(f"영상 파일 처리 중 오류가 발생했습니다: {video_file.name}")

        print(f"\n[{time.ctime()}] 영상 분석을 시작합니다...")

        try:
            # Gemini 모델에 분석 요청
            response = self.model.generate_content(
                [prompt, video_file],
                request_options={'timeout': 600} # 타임아웃 10분 설정
            )

            # 모델 응답에서 JSON 부분만 정리하여 파싱
            json_text = response.text.strip().lstrip("```json").rstrip("```")
            structured_data = json.loads(json_text)
            print(f"[{time.ctime()}] 영상 분석이 성공적으로 완료되었습니다.")
            return structured_data

        except Exception as e:
            print(f"[{time.ctime()}] 모델 분석 중 오류 발생: {e}")
            # 오류 발생 시 업로드된 파일 정리
            genai.delete_file(video_file.name)
            print(f"[{time.ctime()}] 업로드된 파일 ({video_file.name})이 삭제되었습니다.")
            return {"error": str(e), "message": "모델 응답 처리 중 오류가 발생했습니다."} 