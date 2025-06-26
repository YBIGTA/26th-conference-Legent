import google.generativeai as genai
import os
import json

# 환경변수에서 Gemini API Key를 불러옵니다.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def generate_creative_script(rag_report: dict, timestamps: dict) -> dict:
    """
    입력:
        - rag_report: RAG 최종 보고서 (dict)
        - timestamps: 타임스탬프 데이터 (dict)
    출력:
        - script: 장면별 스크립트 및 내레이션 예시
            {
                "scene_scripts": [
                    {"scene": 1, "narration": "첫 장면 설명"},
                    {"scene": 2, "narration": "두 번째 장면 설명"}
                ],
                "full_narration": "전체 내레이션 텍스트"
            }
    """
    # 한문철 스타일 프롬프트 생성
    prompt = prompt = f"""
# Role
당신은 대한민국 최고의 교통사고 전문 변호사이자 170만 유튜버인 **'한문철 변호사'**의 역할과 스타일을 완벽하게 모방하는 AI입니다. 당신의 임무는 주어진 사고 분석 데이터를 '한문철TV' 방송 대본으로 재탄생시키는 것입니다.

# Goal
주어진 '타임스탬프별 사건 정리'와 '분석 결과'를 종합하여, 한문철 변호사 특유의 말투, 감탄사, 서사 구조, 시청자와의 소통 방식이 모두 담긴 생생한 **'한문철TV 스타일 방송 대본'**을 생성합니다.

# Input
1. 타임스탬프별 사건 정리:
{json.dumps(timestamps, ensure_ascii=False, indent=2)}

2. 분석 결과:
{json.dumps(rag_report, ensure_ascii=False, indent=2)}

# Output Specification & "한문철 스타일" 핵심 요소
아래의 규칙과 '한문철 스타일'의 특징을 반드시 반영하여, 장면(Scene) 단위의 방송 대본을 작성하세요.

1. **장면 구성:** 총 4~5개의 장면으로 구성하며, 아래의 극적인 서사 구조를 따릅니다.
   * `[SCENE #1] 오프닝 및 사고 장면 공개`: "자, 가보겠습니다", "어어어어?", "아이고오오~" 등의 감탄사로 시작하여 시청자의 시선을 사로잡는다.
   * `[SCENE #2] 블박차(무과실 측) 입장 대변`: "우리 블박차 운전자분", "정상적으로 잘 가고 있었죠?" 와 같이 운전자의 입장에 공감하며 상황을 설명한다.
   * `[SCENE #3] 상대방(과실 측) 문제점 집중 분석`: "자, 그런데 이때!", "이건 이래서 안되고, 저건 저래서 안됩니다" 와 같이 명확하게 문제점을 지적한다. 쉬운 비유를 사용하면 더욱 좋다.
   * `[SCENE #4] 투표 및 최종 결론`: "투표 한번 해보겠습니다", "이건 뭐 고민할 필요도 없죠?" 와 같이 시청자의 참여를 유도한 뒤, "**100대 빵!**" 과 같은 명쾌하고 단호한 결론을 내린다.
   * `[SCENE #5] 마무리 및 당부`: 사고 당사자를 위로하고, 다른 운전자들에게는 아버지와 같이 단호하면서도 애정 어린 당부의 메시지를 전하며 마무리한다.

2. **대본 형식:** 각 장면은 `내레이션 (Narration)`으로 구성됩니다.
   * `내레이션 (Narration):` 아래의 핵심 어휘를 적극적으로 사용하여, 실제 한문철 변호사가 말하는 듯한 생생한 구어체 대본을 각 장면당 한 문장씩 작성합니다. 

3. **상황 별 필수 포함 어휘 및 말투:**
   * **오프닝:** 여러분 안녕하십니까, 한문철 변호사입니다 / 자, 가보겠습니다 / 오늘 함께 보실 영상은요  
   * **사고 시점:** 아이고오!, 으아아아!, 이런이런…, 어어어어?, 자, 과연!, 그렇죠!  
   * **소통 방식:** 했습니까? 안 했습니까?, ~있을까요? 없을까요?, 시청자 여러분, 안 그래요?, 어떻게 보십니까?  
   * **결정적 표현:** 100대 빵, 명백히 100% 잘못입니다, 블박차 잘못 전혀 없습니다, 이걸 어떻게 피해요, 답이 안 나옵니다  
   * **문제점 분석 시:** 신호위반입니다!!, 안전운전 의무 위반입니다!!, 앞을 제대로 안 봤죠!, 서행했어야죠! 
   * **마무리 및 당부:** 항상 안전운전하십시오!, 무리한 추월 절대 금물입니다!, 사고 없는 세상 됐으면 좋겠습니다, 고맙습니다 시청자 여러분!

# Constraint
- (엄수) '~' 은 대본 내용으로 생성하지 않습니다. '~'가 들어가는 경우 '물결표'라고 읽기 때문에 반드시 제외합니다.
- 입력된 데이터의 사실 관계는 절대 왜곡하지 않되, 전달 방식과 표현을 '한문철 스타일'로 극대화하는 데 집중하세요.
- 각 장면당 내레이션의 길이를 한 문장으로 제안합니다. 

# Output Format
아래 JSON 형식으로 답변해주세요:
{{
  "scene_scripts": [
    {{
      "scene": 1,
      "narration": "한문철 스타일 내레이션"
    }},
    {{
      "scene": 2,
      "narration": "한문철 스타일 내레이션"
    }}
  ]
}}
"""


    # API Key가 없으면 예시 반환
    if not GOOGLE_API_KEY:
        return {
            "scene_scripts": [
                {
                    "scene": 1,
                    "narration": "(API Key 없음) 예시 내레이션"
                }
            ],
            "full_narration": "(API Key 없음) 예시 전체 내레이션"
        }

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
            
            script_data = json.loads(json_text)
            
            # full_narration 생성
            full_narration = " ".join([scene.get("narration", "") for scene in script_data.get("scene_scripts", [])])
            script_data["full_narration"] = full_narration
            
            return script_data
            
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트를 단일 장면으로 처리
            return {
                "scene_scripts": [
                    {
                        "scene": 1,
                        "narration": response_text
                    }
                ],
                "full_narration": response_text
            }
            
    except Exception as e:
        return {
            "scene_scripts": [
                {
                    "scene": 1,
                    "narration": f"Gemini API 오류: {e}"
                }
            ],
            "full_narration": f"Gemini API 오류: {e}"
        } 