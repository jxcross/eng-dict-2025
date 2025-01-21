import streamlit as st
import pandas as pd
from gtts import gTTS
import os
import base64

def text_to_speech(text):
    """텍스트를 음성으로 변환하고 base64로 인코딩된 audio HTML 요소를 반환"""
    try:
        from io import BytesIO
        
        # 메모리에 직접 오디오 생성
        fp = BytesIO()
        tts = gTTS(text=text, lang='en')
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # BytesIO 객체에서 직접 base64 인코딩
        audio_b64 = base64.b64encode(fp.read()).decode()
        fp.close()
        
        # HTML audio 요소 생성
        audio_html = f'''
            <audio id="audio" style="width:100%" controls>
                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
            </audio>
            '''
        return audio_html
    except Exception as e:
        st.error(f"음성 변환 중 오류가 발생했습니다: {str(e)}")
        return None

def load_data(uploaded_file):
    """CSV 또는 Excel 파일을 로드하고 데이터프레임으로 반환"""
    # 새 파일이 업로드되면 세션 상태 초기화
    if 'previous_file' not in st.session_state or st.session_state.previous_file != uploaded_file.name:
        st.session_state.current_index = 0
        st.session_state.user_inputs = {}
        st.session_state.masked_sentences = {}
        st.session_state.hint_levels = {}
        st.session_state.previous_file = uploaded_file.name
        if 'audio_html' in st.session_state:    
            del st.session_state.audio_html     
    
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:  # excel file
        df = pd.read_excel(uploaded_file)
    
    # 컬럼 순서대로 NO, ENG, KOR로 매핑
    if len(df.columns) >= 3:
        df.columns.values[0] = 'NO'
        df.columns.values[1] = 'ENGLISH'
        df.columns.values[2] = 'KOREAN'
    else:
        st.error("파일은 최소 3개의 컬럼이 필요합니다.")
        return None
    
    return df

def is_word_revealed(masked_word, original_word):
    """마스킹된 단어가 원래 단어와 같은지 확인"""
    return masked_word == original_word

def mask_sentence(sentence, current_masked=None, show_all=False, hide_all=False, 
                 show_punctuation=True, show_numbers=True, hint_level=0):
    """문장의 단어들을 마스킹 처리"""
    if show_all:
        return sentence
        
    words = sentence.split()
    current_masked_words = current_masked.split() if current_masked else [""] * len(words)
    masked_words = []
    
    for i, (word, current_mask) in enumerate(zip(words, current_masked_words)):
        # 이미 마스킹이 해제된 단어는 그대로 유지
        if current_mask == word:
            masked_words.append(word)
            continue
            
        masked_word = ""
        for j, char in enumerate(word):
            if hide_all:
                masked_word += "_"
            elif show_punctuation and not char.isalnum():
                masked_word += char
            elif show_numbers and char.isdigit():
                masked_word += char
            elif j < hint_level and char.isalpha():
                masked_word += char
            else:
                masked_word += "_"
        masked_words.append(masked_word)
    
    return " ".join(masked_words)

def unmask_word(masked_sentence, original_sentence, input_text):
    """입력된 단어와 일치하는 마스킹된 단어를 해제"""
    if not input_text:
        return masked_sentence
        
    original_words = original_sentence.split()
    masked_words = masked_sentence.split()
    input_words = input_text.strip().split()
    
    # 입력된 각 단어에 대해 마스킹 해제
    for input_word in input_words:
        for i, (word, masked) in enumerate(zip(original_words, masked_words)):
            # 이미 마스킹이 해제된 단어는 건너뛰기
            if masked == word:
                continue
                
            word_cleaned = ''.join(char.lower() for char in word if char.isalpha())
            input_cleaned = ''.join(char.lower() for char in input_word if char.isalpha())
            if word_cleaned == input_cleaned:
                masked_words[i] = word
            
    return " ".join(masked_words)

def main():
    """메인 함수"""
    st.title("영어 받아쓰기 프로그램")
    
    # 세션 상태 초기화
    if 'current_index' not in st.session_state:
        st.session_state.current_index = 0
    if 'user_inputs' not in st.session_state:
        st.session_state.user_inputs = {}
    if 'masked_sentences' not in st.session_state:
        st.session_state.masked_sentences = {}
    if 'hint_levels' not in st.session_state:
        st.session_state.hint_levels = {}
    if 'previous_file' not in st.session_state:
        st.session_state.previous_file = None
    
    # 사이드바 설정
    with st.sidebar:
        uploaded_file = st.file_uploader("CSV 또는 Excel 파일을 업로드하세요", 
                                       type=['csv', 'xlsx', 'xls'])
        
        show_all = st.checkbox("모두 보이기", value=False)
        hide_all = st.checkbox("모두 감추기", value=False)
        show_punctuation = st.checkbox("구두점 보이기", value=True)
        show_numbers = st.checkbox("숫자 보이기", value=True)
        
        if show_all:
            hide_all = False
            show_punctuation = True
            show_numbers = True
        elif hide_all:
            show_punctuation = False
            show_numbers = False
    
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        
        if df is None:
            return
            
        # 네비게이션 버튼들
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("시작"):
                st.session_state.current_index = 0
                if 'audio_html' in st.session_state:
                    del st.session_state.audio_html
        with col2:
            if st.button("이전") and st.session_state.current_index > 0:
                st.session_state.current_index -= 1
                if 'audio_html' in st.session_state:
                    del st.session_state.audio_html
        with col3:
            if st.button("다음") and st.session_state.current_index < len(df) - 1:
                st.session_state.current_index += 1
                if 'audio_html' in st.session_state:
                    del st.session_state.audio_html
        with col4:
            if st.button("끝"):
                st.session_state.current_index = len(df) - 1
                if 'audio_html' in st.session_state:
                    del st.session_state.audio_html
        
        # 진행 상황 표시
        total_sentences = len(df)
        current_position = st.session_state.current_index + 1
        progress = min(max(current_position / total_sentences, 0.0), 1.0)
        
        st.progress(progress)
        st.write(f"진행 상황: {current_position} / {total_sentences} 문장")
        
        # 현재 문장 정보 표시
        current_row = df.iloc[st.session_state.current_index]
        st.write(f"NO: {current_row['NO']}")
        st.write("Korean:", current_row['KOREAN'])
        
        # 마스킹된 영어 문장 처리
        original_sentence = current_row['ENGLISH']
        
        # Play 버튼과 오디오 플레이어 추가
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Play"):
                audio_html = text_to_speech(original_sentence)
                if audio_html:
                    st.session_state.audio_html = audio_html
        
        with col2:
            if 'audio_html' in st.session_state:
                st.markdown(st.session_state.audio_html, unsafe_allow_html=True)

        # 마스킹된 문장 표시
        st.markdown("English:")
        
        # 현재 인덱스의 마스킹된 문장과 힌트 레벨 초기화
        if st.session_state.current_index not in st.session_state.masked_sentences:
            st.session_state.masked_sentences[st.session_state.current_index] = mask_sentence(
                original_sentence,
                current_masked=None,
                show_all=show_all,
                hide_all=hide_all,
                show_punctuation=show_punctuation,
                show_numbers=show_numbers,
                hint_level=st.session_state.hint_levels.get(st.session_state.current_index, 0)
            )
        if st.session_state.current_index not in st.session_state.hint_levels:
            st.session_state.hint_levels[st.session_state.current_index] = 0
            
        st.markdown(f"```\n{st.session_state.masked_sentences[st.session_state.current_index]}\n```")
        
        # 마스킹이 완전히 해제되지 않은 경우에만 입력 처리
        if st.session_state.masked_sentences[st.session_state.current_index] != original_sentence:
            # 사용자 입력과 입력 처리를 위한 세션 상태 관리
            if f"input_{st.session_state.current_index}" not in st.session_state:
                st.session_state[f"input_{st.session_state.current_index}"] = ""

            def on_input_change():
                current_input = st.session_state[f"input_{st.session_state.current_index}"]
                if current_input:
                    current_masked = unmask_word(
                        st.session_state.masked_sentences[st.session_state.current_index],
                        original_sentence,
                        current_input
                    )
                    st.session_state.masked_sentences[st.session_state.current_index] = current_masked
                    # 입력 필드 초기화
                    st.session_state[f"input_{st.session_state.current_index}"] = ""

            # 사용자 입력
            user_input = st.text_input(
                "단어를 입력하세요 (Enter를 눌러 제출):",
                key=f"input_{st.session_state.current_index}",
                on_change=on_input_change
            )
            
            # 힌트 버튼
            if st.button("힌트"):
                max_length = max(len(word) for word in original_sentence.split())
                if st.session_state.hint_levels[st.session_state.current_index] < max_length:
                    st.session_state.hint_levels[st.session_state.current_index] += 1
                    # 현재 마스킹된 상태를 유지하면서 힌트 적용
                    st.session_state.masked_sentences[st.session_state.current_index] = mask_sentence(
                        original_sentence,
                        current_masked=st.session_state.masked_sentences[st.session_state.current_index],
                        show_all=show_all,
                        hide_all=hide_all,
                        show_punctuation=show_punctuation,
                        show_numbers=show_numbers,
                        hint_level=st.session_state.hint_levels[st.session_state.current_index]
                    )
            
            # "모두 보이기" 선택 시 마스킹 해제
            if show_all:
                st.session_state.masked_sentences[st.session_state.current_index] = original_sentence
            
        # 성공 여부 확인
        if st.session_state.masked_sentences[st.session_state.current_index] == original_sentence:
            st.success("Success! 모든 단어를 맞추셨습니다!")

if __name__ == "__main__":
    main()