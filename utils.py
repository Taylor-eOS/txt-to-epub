import re

def should_add_space(prev_sentence, current_sentence):
    if not prev_sentence:
        return False
    stripped_prev = re.sub(r'[^A-Za-z.!?]+$', '', prev_sentence.strip())
    if re.search(r'[.!?]$', stripped_prev):
        return False
    return True

