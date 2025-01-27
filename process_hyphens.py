import re

def fix_hyphenation(text):
    # Replace the end-of-line hyphen with a space (if it’s followed by a newline and a word)
    text = re.sub(r'-(\n)(\S)', r'\1\2', text)
    
    # Optional: Remove spaces after hyphens if unwanted
    text = text.replace('- ', '')
    
    return text

# Read the input file
with open('input_processed.txt', 'r', encoding='utf-8') as file:
    text = file.read()

# Fix hyphenation
fixed_text = fix_hyphenation(text)

# Write the fixed text to a new file
with open('input_processed_hyphens.txt', 'w', encoding='utf-8') as file:
    file.write(fixed_text)

print("Hyphenation fix applied and saved to 'input_processed_hyphens.txt'.")

