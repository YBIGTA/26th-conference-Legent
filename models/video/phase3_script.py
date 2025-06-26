import google.generativeai as genai
import os
import json
import time
import re
from typing import List

# 환경변수에서 Gemini API Key를 불러옵니다.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def estimate_tts_duration_improved(text: str) -> float:
    """
    개선된 한국어 TTS 길이 추정 함수
    
    Args:
        text: 추정할 텍스트
    
    Returns:
        예상 TTS 길이 (초)
    """
    # 특수 문자와 공백 제거
    clean_text = re.sub(r'[^\w\s가-힣]', '', text)
    
    # 한국어 음절 수 계산 (더 정확한 방법)
    korean_syllables = len(re.findall(r'[가-힣]', clean_text))
    
    # 감탄사와 문장 부호에 따른 속도 조정
    exclamation_count = text.count('!') + text.count('?')
    comma_count = text.count(',') + text.count('，')
    
    # 기본 속도: 3.2음절/초 (더 보수적)
    base_duration = korean_syllables / 3.2
    
    # 감탄사가 있으면 20% 느리게 (감정 표현)
    if exclamation_count > 0:
        base_duration *= 1.2
    
    # 쉼표가 있으면 10% 느리게 (호흡)
    if comma_count > 0:
        base_duration *= (1 + comma_count * 0.05)
    
    # 최소 1초 보장
    return max(base_duration, 1.0)


def adjust_script_for_tts_timing(initial_script: dict, timestamps: dict, target_accident_time: float, max_adjustments: int = 3) -> dict:
    """
    TTS 길이를 기준으로 스크립트를 동적으로 조정하는 함수 (개선된 버전)
    
    Args:
        initial_script: 초기 생성된 스크립트
        timestamps: 타임스탬프 데이터
        target_accident_time: 목표 사고 발생 시점 (초)
        max_adjustments: 최대 조정 횟수
    
    Returns:
        조정된 스크립트
    """
    
    def generate_adjusted_script(adjustment_type: str, current_duration: float, target_duration: float) -> dict:
        """조정된 스크립트 생성 (긴박감 조성 포함)"""
        
        # 목표: 충돌 1초 전에 감탄사가 나오도록 조정
        target_exclamation_time = target_accident_time - 1.0
        
        adjustment_instruction = ""
        if adjustment_type == "shorten":
            time_diff = current_duration - target_duration
            adjustment_instruction = f"""
현재 TTS 길이({current_duration:.1f}초)가 목표 길이({target_duration:.1f}초)보다 {time_diff:.1f}초 길습니다.

**중요한 조정 요구사항:**
1. 스크립트를 {time_diff:.1f}초 정도 짧게 만들어주세요
2. 감탄사('어어어어?', '아이고오오!', '으아아아!')가 정확히 충돌 1초 전({target_exclamation_time:.1f}초)에 나오도록 조정하세요
3. 충돌 직전 긴박감을 조성하는 문장을 포함하세요 (예: "자, 이때!", "그런데 갑자기!", "어? 뭐야?")
4. 한문철 변호사의 말투와 스타일을 유지하세요
"""
        else:  # lengthen
            time_diff = target_duration - current_duration
            adjustment_instruction = f"""
현재 TTS 길이({current_duration:.1f}초)가 목표 길이({target_duration:.1f}초)보다 {time_diff:.1f}초 짧습니다.

**중요한 조정 요구사항:**
1. 스크립트를 {time_diff:.1f}초 정도 길게 만들어주세요
2. 감탄사('어어어어?', '아이고오오!', '으아아아!')가 정확히 충돌 1초 전({target_exclamation_time:.1f}초)에 나오도록 조정하세요
3. 충돌 직전 긴박감을 조성하는 문장을 추가하세요 (예: "자, 이때!", "그런데 갑자기!", "어? 뭐야?")
4. 한문철 변호사의 말투와 스타일을 유지하세요
"""
        
        # 조정된 프롬프트 생성
        adjusted_prompt = f"""
# Role
당신은 대한민국 최고의 교통사고 전문 변호사이자 170만 유튜버인 **'한문철 변호사'**의 역할과 스타일을 완벽하게 모방하는 AI입니다.

# Goal
기존 스크립트를 TTS 타이밍에 맞게 조정하여, **충돌 1초 전에 감탄사가 나오도록** 하고 긴박감을 극대화합니다.

# Current Script
{json.dumps(initial_script, ensure_ascii=False, indent=2)}

# Timing Requirements
- 사고 발생 시점: {target_accident_time}초
- 감탄사 목표 시점: {target_exclamation_time}초 (충돌 1초 전)
- 현재 TTS 길이: {current_duration:.1f}초
- 목표 TTS 길이: {target_duration:.1f}초

# Adjustment Instructions
{adjustment_instruction}

# Critical Requirements
1. **감탄사 타이밍**: 감탄사('어어어어?', '아이고오오!', '으아아아!')가 정확히 충돌 1초 전에 나와야 합니다
2. **긴박감 조성**: 충돌 직전에 "자, 이때!", "그런데 갑자기!", "어? 뭐야?" 같은 긴박감 조성 문구를 포함하세요
3. **한문철 스타일**: 기존의 한문철 변호사 말투와 스타일을 완전히 유지하세요
4. **자연스러운 흐름**: 스크립트의 전체적인 흐름과 내용은 유지하되, 길이와 타이밍만 조정하세요

# Output Format
기존과 동일한 JSON 형식으로 답변해주세요.
"""
        
        try:
            model = genai.GenerativeModel("gemini-2.5-pro")
            response = model.generate_content(adjusted_prompt)
            response_text = response.text.strip()
            
            # JSON 파싱
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text
            
            return json.loads(json_text)
            
        except Exception as e:
            print(f"스크립트 조정 중 오류: {e}")
            return initial_script
    
    # 초기 스크립트의 첫 번째 장면 TTS 길이 추정 (개선된 방법 사용)
    first_scene_narration = initial_script.get("scene_scripts", [{}])[0].get("narration", "")
    current_tts_duration = estimate_tts_duration_improved(first_scene_narration)
    
    # 목표: 충돌 1초 전에 감탄사가 나오도록 조정
    target_exclamation_time = target_accident_time - 1.0
    
    print(f"🎯 TTS 타이밍 조정 시작 (개선된 버전):")
    print(f"   - 사고 발생 시점: {target_accident_time}초")
    print(f"   - 감탄사 목표 시점: {target_exclamation_time}초 (충돌 1초 전)")
    print(f"   - 현재 TTS 길이: {current_tts_duration:.1f}초")
    print(f"   - 목표 TTS 길이: {target_exclamation_time:.1f}초")
    print(f"   - 차이: {abs(current_tts_duration - target_exclamation_time):.1f}초")
    
    # 조정이 필요한지 확인 (0.5초 이상 차이나는 경우 - 더 엄격한 기준)
    if abs(current_tts_duration - target_exclamation_time) < 0.5:
        print("✅ TTS 타이밍이 적절합니다. 조정 불필요.")
        return initial_script
    
    adjusted_script = initial_script
    
    for attempt in range(max_adjustments):
        print(f"🔄 조정 시도 {attempt + 1}/{max_adjustments}")
        
        # 조정 방향 결정
        if current_tts_duration > target_exclamation_time:
            adjustment_type = "shorten"
        else:
            adjustment_type = "lengthen"
        
        # 스크립트 조정
        adjusted_script = generate_adjusted_script(
            adjustment_type, 
            current_tts_duration, 
            target_exclamation_time
        )
        
        # 조정된 스크립트의 TTS 길이 재계산
        new_first_scene_narration = adjusted_script.get("scene_scripts", [{}])[0].get("narration", "")
        new_tts_duration = estimate_tts_duration_improved(new_first_scene_narration)
        
        print(f"   - 조정 후 TTS 길이: {new_tts_duration:.1f}초")
        print(f"   - 새로운 차이: {abs(new_tts_duration - target_exclamation_time):.1f}초")
        
        # 목표에 도달했는지 확인 (0.5초 이내)
        if abs(new_tts_duration - target_exclamation_time) < 0.5:
            print("✅ TTS 타이밍 조정 완료! (감탄사가 충돌 1초 전에 배치됨)")
            break
        
        current_tts_duration = new_tts_duration
    
    # full_narration 업데이트
    full_narration = " ".join([scene.get("narration", "") for scene in adjusted_script.get("scene_scripts", [])])
    adjusted_script["full_narration"] = full_narration
    
    return adjusted_script


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
    
    # 타임스탬프 데이터 분석하여 사고 발생 시점 파악
    accident_time = None
    accident_description = ""
    
    if timestamps and "events" in timestamps:
        for event in timestamps["events"]:
            description = event.get("description", "").lower()
            # 사고/충돌 관련 키워드 검색 (더 포괄적으로)
            accident_keywords = ["충돌", "사고", "진입", "횡단", "돌진", "부딪", "맞닥뜨", "접촉", "충격", "추돌"]
            if any(keyword in description for keyword in accident_keywords):
                # 시간을 초 단위로 변환
                start_time = event.get("start", "00:00")
                try:
                    minutes, seconds = map(int, start_time.split(":"))
                    accident_time = minutes * 60 + seconds
                    accident_description = event.get("description", "")
                    break
                except:
                    continue
    
    # 사고 발생 시점에 따른 오프닝 전략 결정 (개선된 버전)
    if accident_time is not None:
        if accident_time <= 3:
            opening_strategy = "즉시_감탄사"
            opening_instruction = "사고가 3초 이내에 발생하므로, '자, 가보겠습니다' 이후에 바로 긴박감 조성 문구와 감탄사를 사용하여 시청자의 시선을 사로잡으세요."
        elif accident_time <= 7:
            opening_strategy = "빠른_긴박감"
            opening_instruction = "사고가 4~7초 후에 발생하므로, 짧은 인사 후 바로 긴박감 조성 문구('자, 이때!', '그런데 갑자기!')와 감탄사를 포함하세요."
        elif accident_time <= 12:
            opening_strategy = "중간_긴박감"
            opening_instruction = "사고가 8~12초 후에 발생하므로, 일반적인 오프닝을 사용하되 사고 발생 1초 전에 긴박감 조성 문구와 감탄사를 강조하세요."
        else:
            opening_strategy = "일반_긴박감"
            opening_instruction = "사고가 12초 이후에 발생하므로, 일반적인 오프닝을 사용하되 사고 발생 1초 전에 긴박감 조성 문구와 감탄사를 포함하세요."
    else:
        opening_strategy = "기본_긴박감"
        opening_instruction = "사고 발생 시점을 정확히 파악할 수 없으므로, 일반적인 오프닝을 사용하되 긴박감 조성 문구와 감탄사를 포함하세요."
    
    # 타임스탬프 정보를 읽기 쉬운 형태로 변환
    timestamp_info = ""
    if timestamps and "events" in timestamps:
        timestamp_info = "## 타임스탬프별 사건 진행:\n"
        for i, event in enumerate(timestamps["events"], 1):
            start = event.get("start", "N/A")
            end = event.get("end", "N/A")
            description = event.get("description", "N/A")
            timestamp_info += f"- {start}~{end}: {description}\n"
    
    # 한문철 스타일 프롬프트 생성 (개선된 버전)
    prompt = f"""
# Role
당신은 대한민국 최고의 교통사고 전문 변호사이자 170만 유튜버인 **'한문철 변호사'**의 역할과 스타일을 완벽하게 모방하는 AI입니다. 당신의 임무는 주어진 사고 분석 데이터를 '한문철TV' 방송 대본으로 재탄생시키는 것입니다.

# Goal
주어진 '타임스탬프별 사건 정리'와 '분석 결과'를 종합하여, 한문철 변호사 특유의 말투, 감탄사, 서사 구조, 시청자와의 소통 방식이 모두 담긴 생생한 **'한문철TV 스타일 방송 대본'**을 생성합니다.

# Input
1. 타임스탬프별 사건 정리:
{timestamp_info}

2. 분석 결과:
{json.dumps(rag_report, ensure_ascii=False, indent=2)}

3. 사고 발생 시점 분석:
- 사고 발생 시점: {accident_time}초
- 사고 발생 상황: {accident_description}
- 오프닝 전략: {opening_strategy}
- 오프닝 지침: {opening_instruction}

# Output Specification & "한문철 스타일" 핵심 요소
아래의 규칙과 '한문철 스타일'의 특징을 반드시 반영하여, 장면(Scene) 단위의 방송 대본을 작성하세요.

1. **장면 구성:** 총 4~5개의 장면으로 구성하며, 아래의 극적인 서사 구조를 따릅니다.
   * `[SCENE #1] 오프닝 및 사고 장면 공개`: {opening_instruction} **중요: 사고 발생 1초 전에 긴박감 조성 문구('자, 이때!', '그런데 갑자기!')와 감탄사를 사용**하여 시청자의 시선을 사로잡는다.
   * `[SCENE #2] 블박차(무과실 측) 입장 대변`: "우리 블박차 운전자분", "정상적으로 잘 가고 있었죠?" 와 같이 운전자의 입장에 공감하며 상황을 설명한다.
   * `[SCENE #3] 상대방(과실 측) 문제점 집중 분석`: "자, 그런데 이때!", "이건 이래서 안되고, 저건 저래서 안됩니다" 와 같이 명확하게 문제점을 지적한다. 쉬운 비유를 사용하면 더욱 좋다.
   * `[SCENE #4] 투표 및 최종 결론`: "투표 한번 해보겠습니다", "이건 뭐 고민할 필요도 없죠?" 와 같이 시청자의 참여를 유도한 뒤, 명쾌하고 단호한 결론을 내린다.
   * `[SCENE #5] 마무리 및 당부`: 사고 당사자를 위로하고, 다른 운전자들에게는 아버지와 같이 단호하면서도 애정 어린 당부의 메시지를 전하며 마무리한다.

2. **대본 형식:** 각 장면은 `내레이션 (Narration)`으로 구성됩니다.
   * `내레이션 (Narration):` 아래의 핵심 어휘를 적극적으로 사용하여, 실제 한문철 변호사가 말하는 듯한 생생한 구어체 대본을 각 장면당 한 문장씩 작성합니다. 

3. **상황 별 필수 포함 어휘 및 말투:**
   * **오프닝:** 여러분 안녕하십니까, 한문철 변호사입니다 / 자, 가보겠습니다 / 오늘 함께 보실 영상은요  
   * **긴박감 조성:** 자, 이때! / 그런데 갑자기! / 어? 뭐야? / 잠깐만요! / 이건 뭐야?
   * **사고 시점 감탄사:** 아이고오!, 으아아아!, 이런이런…, 어어어어?, 자, 과연!, 그렇죠!  
   * **소통 방식:** 했습니까? 안 했습니까?, ~있을까요? 없을까요?, 시청자 여러분, 안 그래요?, 어떻게 보십니까?  
   * **결정적 표현:** 명백히 잘못입니다, 블박차 잘못 전혀 없습니다, 이걸 어떻게 피해요, 답이 안 나옵니다  
   * **문제점 분석 시:** 신호위반입니다!!, 안전운전 의무 위반입니다!!, 앞을 제대로 안 봤죠!, 서행했어야죠! 
   * **마무리 및 당부:** 항상 안전운전하십시오!, 무리한 추월 절대 금물입니다!, 사고 없는 세상 됐으면 좋겠습니다, 고맙습니다 시청자 여러분!

# Constraint
- (엄수) '3. 상황 별 필수 포함 어휘 및 말투'에서, 최소한 하나를 포함하여 제작한다.
- (엄수) **사고 발생 1초 전에 긴박감 조성 문구와 감탄사를 사용**하여 극적인 효과를 극대화한다.
- (엄수) '~' 은 대본 내용으로 생성하지 않습니다. '~'가 들어가는 경우 '물결표'라고 읽기 때문에 반드시 제외합니다.
- (엄수) **충돌 전 시점부터 충돌 시점까지의 긴박감을 고조시키는 내레이션**을 작성한다.
- 입력된 데이터의 사실 관계는 절대 왜곡하지 않되, 전달 방식과 표현을 '한문철 스타일'로 극대화하는 데 집중하세요.
- 각 장면당 내레이션의 길이를 한 문장으로 제안합니다. 

# Output Format
아래 JSON 형식으로 답변해주세요:
{{
  "scene_scripts": [
    {{
      "scene": 1,
      "narration": "한문철 스타일 내레이션 (긴박감 조성 + 감탄사 포함)"
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
            
            # TTS 타이밍 조정 (사고 발생 시점이 있는 경우)
            if accident_time is not None:
                print(f"🎬 TTS 타이밍 조정 시작 - 사고 시점: {accident_time}초")
                script_data = adjust_script_for_tts_timing(script_data, timestamps, accident_time)
            
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