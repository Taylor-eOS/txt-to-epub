import re

def process_file():
    input_file = "input.txt"
    output_file = "input_page.txt"
    with open(input_file, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]
    page_re = re.compile(r"^<\s*(\d+)\s*>$")
    blocks = []
    current_content = []
    for line_num, line in enumerate(lines, 1):
        if line.strip() == "":
            continue
        m = page_re.fullmatch(line)
        if m:
            if not current_content:
                raise ValueError(f"Malformed input: Page number encountered without preceding content (line {line_num}).")
            try:
                page = int(m.group(1))
            except Exception:
                raise ValueError(f"Malformed input: Cannot parse page number on line {line_num}.")
            blocks.append({"content": current_content, "orig_page": page, "line_num": line_num})
            current_content = []
        else:
            current_content.append(line)
    if current_content:
        raise ValueError("Malformed input: File ended before a page number was found for the last block.")
    series_offset = 0
    current_series_max = None
    for idx, block in enumerate(blocks):
        orig = block["orig_page"]
        if idx == 0:
            if orig != 1:
                raise ValueError(f"Malformed input: The first block must start with page number 1 (block starting at line {block['line_num']}).")
            current_series_max = orig
        else:
            prev = blocks[idx - 1]["orig_page"]
            if orig < prev:
                series_offset += current_series_max
                current_series_max = orig
            else:
                if orig > current_series_max:
                    current_series_max = orig
        block["new_page"] = series_offset + orig
    with open(output_file, "w", encoding="utf-8") as f:
        for block in blocks:
            for line in block["content"]:
                f.write(f"{line}\n")
            f.write(f"<{block['new_page']}>\n\n")

if __name__ == "__main__":
    process_file()

