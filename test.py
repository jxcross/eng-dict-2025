
masked_sentence="good morning _________ _____ _____ ____ _ _______"
original_sentence = "good morning everybody today feels like a holiday"
input_text="like"
unmasked_words = set(["morning", "good"])


original_words = original_sentence.split()
masked_words = masked_sentence.split()
input_word = input_text.strip().lower()

# 입력된 단어와 일치하는 단어들의 인덱스를 unmasked_words에 추가
for i, word in enumerate(original_words):
    if word.lower() == input_word:
        unmasked_words.add(i)

# 마스킹이 해제된 단어들을 표시
for i in range(len(masked_words)):
    if i in unmasked_words:
        masked_words[i] = original_words[i]
        
print(" ".join(masked_words))



sentence = "hello I've been waiting for you"
words = sentence.split()
for word in words:
    print(word)