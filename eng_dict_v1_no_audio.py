import streamlit as st
import pandas as pd

def load_data(uploaded_file):
    # 새 파일이 업로드되면 세션 상태 초기화
    if 'previous_file' not in st.session_state or st.session_state.previous_file != uploaded_file.name:
        st.session_state.current_index = 0
        st.session_state.user_inputs = {}
        st.session_state.masked_sentences = {}
        st.session_state.hint_levels = {}
        st.session_state.previous_file = uploaded_file.name
    
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
        with col2:
            if st.button("이전") and st.session_state.current_index > 0:
                st.session_state.current_index -= 1
        with col3:
            if st.button("다음") and st.session_state.current_index < len(df) - 1:
                st.session_state.current_index += 1
        with col4:
            if st.button("끝"):
                st.session_state.current_index = len(df) - 1
        
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
        
        # 현재 인덱스의 마스킹된 문장과 힌트 레벨 초기화
        if st.session_state.current_index not in st.session_state.masked_sentences:
            st.session_state.masked_sentences[st.session_state.current_index] = mask_sentence(
                original_sentence,
                current_masked=None,
                show_all=False,
                hide_all=hide_all,
                show_punctuation=show_punctuation,
                show_numbers=show_numbers,
                hint_level=st.session_state.hint_levels.get(st.session_state.current_index, 0)
            )
        if st.session_state.current_index not in st.session_state.hint_levels:
            st.session_state.hint_levels[st.session_state.current_index] = 0
        


        # 마스킹이 완전히 해제되지 않은 경우에만 입력 처리
        if st.session_state.masked_sentences[st.session_state.current_index] != original_sentence:
            # 사용자 입력
            user_input = st.text_input("단어를 입력하세요:",
                                     key=f"input_{st.session_state.current_index}")
            
            # 힌트 버튼
            if st.button("힌트"):
                max_length = max(len(word) for word in original_sentence.split())
                if st.session_state.hint_levels[st.session_state.current_index] < max_length:
                    st.session_state.hint_levels[st.session_state.current_index] += 1
                    # 현재 마스킹된 상태를 유지하면서 힌트 적용
                    st.session_state.masked_sentences[st.session_state.current_index] = mask_sentence(
                        original_sentence,
                        current_masked=st.session_state.masked_sentences[st.session_state.current_index],
                        show_all=False,
                        hide_all=hide_all,
                        show_punctuation=show_punctuation,
                        show_numbers=show_numbers,
                        hint_level=st.session_state.hint_levels[st.session_state.current_index]
                    )
            
            # 입력된 단어로 마스킹 해제
            if user_input:
                current_masked = unmask_word(
                    st.session_state.masked_sentences[st.session_state.current_index],
                    original_sentence,
                    user_input
                )
                st.session_state.masked_sentences[st.session_state.current_index] = current_masked
            
            # "모두 보이기" 선택 시 마스킹 해제
            if show_all:
                st.session_state.masked_sentences[st.session_state.current_index] = original_sentence

        # 마스킹된 문장 표시
        st.markdown("English:")
        st.markdown(f"```\n{st.session_state.masked_sentences[st.session_state.current_index]}\n```")

        # 성공 여부 확인
        if st.session_state.masked_sentences[st.session_state.current_index] == original_sentence:
            st.success("Success! 모든 단어를 맞추셨습니다!")

if __name__ == "__main__":
    main()