class Block:
    def __init__(self, lines):
        self.type = None
        self.content = ""
        self.page_number = ""
        self.to_remove = False
        self.parse_lines(lines)

    def parse_lines(self, lines):
        lines = [line.strip() for line in lines if line.strip()]
        if not lines:
            return
        first_line = lines[0]
        if first_line.startswith('<') and '>' in first_line:
            end_tag_index = first_line.find('>')
            self.type = first_line[1:end_tag_index].lower()
            content = first_line[end_tag_index + 1:].strip()
            if content:
                self.content = content
        for line in lines[1:]:
            if line.startswith('</') and line.endswith('>'):
                continue
            elif line.startswith('<') and line.endswith('>') and not self.page_number:
                self.page_number = line[1:-1].strip()  # Extract page number without angle brackets
            else:
                if self.content:
                    self.content += ' ' + line.strip()
                else:
                    self.content = line.strip()

    def clean_content(self):
        self.content = self.content.strip()

    def to_lines(self):
        if self.to_remove:
            return []
        content = self.content.strip()
        tag_line = f"<{self.type}>{content}"
        lines = [tag_line, f"</{self.type}>"]  # Use the correct closing tag
        if self.page_number:
            lines.append(f"<{self.page_number}>")  # Ensure consistent formatting
        return lines


def parse_blocks(file_content):
    blocks = []
    current_block = []
    for line in file_content:
        if line.strip() == '':
            if current_block:
                blocks.append(Block(current_block))
                current_block = []
        else:
            current_block.append(line.rstrip('\n'))
    if current_block:
        blocks.append(Block(current_block))
    return blocks


def clean_blocks(blocks):
    for block in blocks:
        block.clean_content()
    return blocks


def combine_consecutive_headers(blocks):
    combined_blocks = []
    i = 0
    while i < len(blocks):
        current_block = blocks[i]
        if current_block.type == 'h1':
            combined_content = current_block.content
            j = i + 1
            while j < len(blocks) and blocks[j].type == 'h1':
                combined_content += ' ' + blocks[j].content
                blocks[j].to_remove = True
                j += 1
            current_block.content = combined_content
        combined_blocks.append(current_block)
        i += 1
    return combined_blocks


def merge_drop_caps(blocks):
    """
    Merge drop cap blocks (single-letter 'body' blocks) with the following 'body' block.
    """
    i = 0
    while i < len(blocks) - 1:
        current_block = blocks[i]
        next_block = blocks[i + 1]
        if current_block.type == 'body' and len(current_block.content) == 1 and next_block.type == 'body':
            # Merge drop cap into the next body block without space
            next_block.content = current_block.content + next_block.content
            current_block.to_remove = True
            i += 2  # Skip the next block since it's already merged
        else:
            i += 1
    return blocks


def merge_split_blocks(blocks):
    """
    Merge 'body' blocks that are split across pages, even if there are intervening non-body blocks like footnotes.
    """
    i = 0
    while i < len(blocks):
        current_block = blocks[i]
        if current_block.type == 'body':
            # Initialize a reference to the current body block
            last_body = current_block
            j = i + 1
            while j < len(blocks):
                next_block = blocks[j]
                if next_block.type == 'body':
                    # Check if the next body block is on a different page
                    if last_body.page_number and next_block.page_number and last_body.page_number != next_block.page_number:
                        # Merge the next body block into the last_body
                        last_body.content += ' ' + next_block.content
                        last_body.page_number = next_block.page_number  # Update to the new page number
                        next_block.to_remove = True
                        # Continue searching for more split parts
                        last_body = last_body  # Remains the same
                        j += 1
                    else:
                        # Same page or missing page number; no merge
                        break
                else:
                    # Non-body block; skip and continue
                    j += 1
            i = j
        else:
            i += 1
    return blocks


def process_blocks(blocks):
    blocks = clean_blocks(blocks)
    blocks = combine_consecutive_headers(blocks)
    blocks = merge_drop_caps(blocks)
    blocks = merge_split_blocks(blocks)
    return blocks


def write_output(blocks, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for block in blocks:
            lines = block.to_lines()
            for line in lines:
                f.write(line + '\n')
            if not block.to_remove:
                f.write('\n')


def main():
    input_file = 'input.txt'
    output_file = 'input_processed.txt'
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            file_content = file.readlines()
        blocks = parse_blocks(file_content)
        processed_blocks = process_blocks(blocks)
        write_output(processed_blocks, output_file)
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()

