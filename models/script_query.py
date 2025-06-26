import os
import json
from dotenv import load_dotenv
from .hypergraphrag.hypergraphrag import HyperGraphRAG

def run_rag_on_accident_json(
    accident_json_path=None,
    extra_query=None,
    working_dir="data/graph"
):
    # 환경변수 로드
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)

    # 기본 경로/쿼리
    if accident_json_path is None:
        accident_json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'jsons', 'tmp_result.json')
    if extra_query is None:
        extra_query = (
            "제공된 교통사고 정보를 바탕으로, 사고 당사자(자동차, 자전거)의 유형과 각자의 운행 방식(직진, 무단횡단), 신호 위반 여부, "
            "충돌 지점(횡단보도), 환경적 요인(시야 제한)을 종합적으로 고려하여 가장 적합한 사고 유형을 분류합니다. "
            "특히 '자동차와 이륜차의 사고' 장 내에서 신호 위반 및 횡단보도와 관련된 도표들을 중점적으로 검색하고, "
            "해당 도표의 상세 내용을 추출하여 최종 과실 비율을 판단합니다."
        )

    # 분석 결과 JSON 읽기
    if not os.path.exists(accident_json_path):
        raise FileNotFoundError(f"{accident_json_path} 파일이 존재하지 않습니다. 분석을 먼저 실행하세요.")
    with open(accident_json_path, 'r', encoding='utf-8') as f:
        accident_info = json.load(f)

    # 쿼리 생성
    query_text = json.dumps(accident_info, ensure_ascii=False, indent=2) + "\n" + extra_query

    # RAG 실행
    rag = HyperGraphRAG(working_dir=working_dir)
    result = rag.query(query_text)
    return result