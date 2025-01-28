import re

def process_hyphenated_blocks(text):
    """
    Process hyphenated blocks and merge words split across lines.
    """
    lines = text.splitlines()
    fixed_lines = []
    i = 0
    changes_made = False  # Track if we made changes in this pass

    while i < len(lines):
        current_line = lines[i].strip()

        if current_line.endswith('-'):  # Found a hyphenated word
            word_start = current_line.rstrip('-')

            # Check for the expected block structure
            if (i + 1 < len(lines) and lines[i + 1].strip() == '</body>' and
                i + 2 < len(lines) and re.match(r'<\d+>', lines[i + 2].strip()) and
                i + 3 < len(lines) and lines[i + 3].strip() == '' and
                i + 4 < len(lines) and lines[i + 4].startswith('<body>')):

                # Extract the continuation of the word
                word_end = lines[i + 4].replace('<body>', '').strip()
                fixed_lines.append(word_start + word_end)  # Merge and add to results
                changes_made = True  # Note that a change was made

                # Skip the processed lines
                i += 4
            else:
                # Unexpected structure; keep the current line as-is
                fixed_lines.append(current_line)
        else:
            # Regular line; add it as-is
            fixed_lines.append(current_line)

        i += 1

    # Join lines back into text
    return '\n'.join(fixed_lines), changes_made


def iterative_fix_hyphenation(text):
    """
    Repeat hyphenation fixes until no more changes are made.
    """
    while True:
        text, changes_made = process_hyphenated_blocks(text)
        if not changes_made:  # Stop if no changes were made
            break
    return text


# Read input text
with open('input_processed.txt', 'r', encoding='utf-8') as file:
    text = file.read()

# Iteratively fix hyphenation
fixed_text = iterative_fix_hyphenation(text)

# Write the result to an output file
with open('input_processed_hyphens.txt', 'w', encoding='utf-8') as file:
    file.write(fixed_text)

print("Hyphenation fixed and text saved")

