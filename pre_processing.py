import re

allowed_tags = {"body", "h1", "h2", "h3", "blockquote", "footer"}

def remove_leading(line):
    while line and line[0] in " \t":
        line = line[1:]
    return line

def join_line_pair(current_line, next_line):
    trimmed = current_line.rstrip(" \t")
    if trimmed.endswith("-"):
        return trimmed[:-1] + next_line
    elif current_line.endswith(" "):
        return current_line + next_line
    elif current_line and current_line[-1].isalpha():
        return current_line + " " + next_line
    else:
        return current_line + " " + next_line

def join_lines_in_block(block_lines):
    lines = [remove_leading(line.rstrip("\n")) for line in block_lines]
    if not lines:
        return ""
    joined = lines[0]
    for line in lines[1:]:
        joined = join_line_pair(joined, line)
    return joined

def process_text_block(block_lines, tag):
    if len(block_lines) == 1:
        line = block_lines[0].rstrip("\n")
        pattern = re.compile(rf'^<{tag}>(.*)</{tag}>$')
        m = pattern.match(line)
        if m:
            content = m.group(1)
            return f"<{tag}>{content}</{tag}>\n"
        else:
            return line + "\n"
    else:
        stripped_lines = [l.rstrip("\n") for l in block_lines]
        first_line = stripped_lines[0]
        open_tag_end = first_line.find(">")
        opening_tag = first_line[:open_tag_end+1]
        first_text = first_line[open_tag_end+1:]
        last_line = stripped_lines[-1]
        close_tag_start = last_line.rfind("<")
        closing_tag = last_line[close_tag_start:]
        last_text = last_line[:close_tag_start]
        middle_lines = stripped_lines[1:-1]
        content_lines = []
        if first_text:
            content_lines.append(first_text)
        content_lines.extend(middle_lines)
        if last_text:
            content_lines.append(last_text)
        joined_content = join_lines_in_block(content_lines)
        return opening_tag + joined_content + closing_tag + "\n"

def process_file(file_path='input.txt', output_path='input_pre.txt'):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    output_lines = []
    inside_block = False
    current_block_lines = []
    current_tag = None
    for line in lines:
        if not inside_block:
            found_tag = None
            for tag in allowed_tags:
                if line.lstrip().startswith(f"<{tag}>"):
                    found_tag = tag
                    break
            if found_tag:
                current_tag = found_tag
                current_block_lines = [line]
                if f"</{current_tag}>" in line:
                    processed = process_text_block(current_block_lines, current_tag)
                    output_lines.append(processed)
                    current_block_lines = []
                    current_tag = None
                else:
                    inside_block = True
            else:
                output_lines.append(line)
        else:
            current_block_lines.append(line)
            if f"</{current_tag}>" in line:
                processed = process_text_block(current_block_lines, current_tag)
                output_lines.append(processed)
                inside_block = False
                current_block_lines = []
                current_tag = None

    # New step to handle '-</tag>' cases
    i = 0
    while i < len(output_lines):
        line = output_lines[i].rstrip('\n')  # Process without newline
        # Check if the line matches a block tag with content ending in '-'
        pattern = re.compile(r'^<({})>(.*)</\1>$'.format('|'.join(allowed_tags)))
        m = pattern.match(line)
        if m:
            tag = m.group(1)
            content = m.group(2)
            if content.endswith('-'):
                # Split content to remove hyphen and move the preceding part
                content_without_hyphen = content[:-1]
                last_space = content_without_hyphen.rfind(' ')
                if last_space == -1:
                    current_content = ''
                    moved_part = content_without_hyphen
                else:
                    current_content = content_without_hyphen[:last_space + 1]
                    moved_part = content_without_hyphen[last_space + 1:]
                # Update current line
                new_line = f"<{tag}>{current_content}</{tag}>\n"
                output_lines[i] = new_line
                # Find the next occurrence of the same tag
                j = i + 1
                found = False
                while j < len(output_lines):
                    next_line = output_lines[j].rstrip('\n')
                    m_next = pattern.match(next_line)
                    if m_next and m_next.group(1) == tag:
                        # Modify the next block's content
                        next_content = m_next.group(2)
                        new_next_content = moved_part + next_content
                        new_next_line = f"<{tag}>{new_next_content}</{tag}>\n"
                        output_lines[j] = new_next_line
                        found = True
                        break
                    j += 1
                if not found:
                    pass  # Handle cases where no next block is found if necessary
        i += 1

    with open(output_path, 'w') as out_file:
        out_file.writelines(output_lines)

if __name__ == "__main__":
    process_file()
