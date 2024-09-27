import re

def continues_block(prev_sentence, current_sentence):
    continues_word = False
    continues_sentence = False
    new_sentence = False

    end_punctuations = re.compile(r'[\.\!\?]["\']?$')
    if not end_punctuations.search(prev_sentence):
        continues_word = True
    if re.search(r'\d+$', prev_sentence.strip()):
        continues_sentence = True
    if not continues_word and not continues_sentence:
        new_sentence = True

    if continues_word:
        return 'continues_word'
    elif continues_sentence:
        return 'continues_sentence'
    else:
        return 'new_sentence'

