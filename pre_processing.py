def parse_blocks(file_content):
    blocks = []
    block = []
    for line in file_content:
        if line.strip() == '':
            if block:
                blocks.append(block)
                block = []
        else:
            block.append(line.rstrip('\n'))
    if block:
        blocks.append(block)
    return blocks

def process_blocks(blocks):
    output_blocks = []
    i = 0
    while i < len(blocks):
        current_block = blocks[i]
        if current_block and current_block[0].startswith('<body>'):
            # Extract content from current block
            content_lines = current_block[0][6:] + '\n' + '\n'.join(current_block[1:-2])
            content = content_lines.strip()
            if len(content) == 1 and i + 1 < len(blocks):
                next_block = blocks[i + 1]
                if next_block and next_block[0].startswith('<body>'):
                    # Merge the single character with the next block's content
                    next_content_lines = next_block[0][6:] + '\n' + '\n'.join(next_block[1:-2])
                    merged_content = content + next_content_lines
                    # Reconstruct the merged block
                    merged_block = [
                        '<body>' + merged_content.strip(),
                        next_block[-2],  # </end>
                        next_block[-1]   # <number>
                    ]
                    output_blocks.append(merged_block)
                    i += 2  # Skip the next block as it's merged
                    continue
        # If no merge happened, just add the current block
        output_blocks.append(current_block)
        i += 1
    return output_blocks

def write_output(output_blocks, output_file):
    with open(output_file, 'w') as f:
        for block in output_blocks:
            for line in block:
                f.write(line + '\n')
            f.write('\n')  # Add a blank line between blocks

# Read the input file
with open('input.txt', 'r') as file:
    file_content = file.readlines()

# Parse, process, and write the output
blocks = parse_blocks(file_content)
output_blocks = process_blocks(blocks)
write_output(output_blocks, 'output_p.txt')

