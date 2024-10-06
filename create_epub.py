import os
import zipfile
import uuid
import re
import sys
import shutil
from pathlib import Path
from utils import should_add_space
from epub_strings import (
    STYLESHEET_CONTENT,
    CONTAINER_XML,
    COVER_XHTML,
    NCX_TEMPLATE,
    CONTENT_OPF_TEMPLATE,
    XHTML_TEMPLATE
)

def create_epub():
    book_title = "Book Title"
    author = "Author Name"
    language = "en"
    cover_image = 'cover.jpg' if Path('cover.jpg').is_file() else None
    unique_id = str(uuid.uuid4())

    def parse_input(txt_file):
        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        chapters = []
        chapter_data = {'title': None, 'blocks': [], 'footnotes': []}
        current_tag = None
        block_content = []
        current_page = None
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('<h1>'):
                new_title = line[len('<h1>'):].strip()
                if not chapter_data['blocks'] and not chapter_data['footnotes']:
                    if chapter_data['title']:
                        chapter_data['title'] += ' ' + new_title
                    else:
                        chapter_data['title'] = new_title
                else:
                    chapters.append(chapter_data)
                    chapter_data = {'title': new_title, 'blocks': [], 'footnotes': []}
                current_tag = None
                block_content = []
            elif line.startswith('<body>'):
                current_tag = 'body'
                block_content.append(line[len('<body>'):].strip())
            elif line.startswith('<footer>'):
                current_tag = 'footer'
                block_content.append(line[len('<footer>'):].strip())
            elif line.startswith('<blockquote>'):
                current_tag = 'blockquote'
                block_content.append(line[len('<blockquote>'):].strip())
            elif line == '</end>':
                i += 1
                if i < len(lines):
                    page_line = lines[i].strip()
                    if page_line.startswith('<') and page_line.endswith('>'):
                        page_number = page_line[1:-1]
                        current_page = page_number
                block_text = ' '.join(block_content)
                if current_tag == 'body' or current_tag == 'blockquote':
                    chapter_data['blocks'].append((current_tag, block_text, current_page))
                elif current_tag == 'footer':
                    chapter_data['footnotes'].append(block_text)
                block_content = []
                current_tag = None
            else:
                if current_tag:
                    block_content.append(line)
            i += 1
        if chapter_data['title'] or chapter_data['blocks'] or chapter_data['footnotes']:
            chapters.append(chapter_data)
        return chapters

    def create_chapter_files(chapters):
        for i, chapter in enumerate(chapters, start=1):
            content = ""
            previous_page = None
            current_paragraph = ""
            for block in chapter.get('blocks', []):
                tag, block_text, current_page = block
                block_text = block_text.strip()
                if not block_text:
                    continue
                if tag == 'blockquote':
                    if current_paragraph:
                        content += f'<p>{current_paragraph.strip()}</p>\n'
                        current_paragraph = ""
                    content += f'<blockquote>{block_text}</blockquote>\n'
                elif tag == 'body':
                    if previous_page is not None and current_page is not None and previous_page != current_page:
                        current_paragraph += ' ' + block_text
                    else:
                        if current_paragraph:
                            content += f'<p>{current_paragraph.strip()}</p>\n'
                        current_paragraph = block_text
                previous_page = current_page
            if current_paragraph:
                content += f'<p>{current_paragraph.strip()}</p>\n'
            if chapter.get('footnotes'):
                content += '<div class="footer">\n'
                for footnote in chapter['footnotes']:
                    content += f'<p>{footnote}</p>\n'
                content += '</div>\n'
            xhtml_content = XHTML_TEMPLATE.format(title=chapter["title"], content=content)
            filename = f"chapter{i}.xhtml"
            chapter_path = os.path.join('OEBPS', filename)
            with open(chapter_path, 'w', encoding='utf-8') as file:
                file.write(xhtml_content)

    def create_stylesheet():
        stylesheet_path = os.path.join('OEBPS', 'stylesheet.css')
        with open(stylesheet_path, 'w', encoding='utf-8') as file:
            file.write(STYLESHEET_CONTENT)

    def create_toc_ncx(chapters):
        nav_points = '\n'.join([
            f'''<navPoint id="navPoint-{i}" playOrder="{i}">
      <navLabel>
        <text>{chapter["title"]}</text>
      </navLabel>
      <content src="chapter{i}.xhtml"/>
    </navPoint>''' for i, chapter in enumerate(chapters, start=1)
        ])
        toc_ncx = NCX_TEMPLATE.format(unique_id=unique_id, book_title=book_title, nav_points=nav_points)
        toc_ncx_path = os.path.join('OEBPS', 'toc.ncx')
        if not Path(toc_ncx_path).is_file():
            with open(toc_ncx_path, 'w', encoding='utf-8') as file:
                file.write(toc_ncx)

    def create_content_opf(chapters):
        manifest_items = '\n'.join([
            f'<item id="chapter{i}" href="chapter{i}.xhtml" media-type="application/xhtml+xml"/>' 
            for i in range(1, len(chapters) + 1)
        ])
        spine_items = '\n'.join([
            f'<itemref idref="chapter{i}"/>' for i in range(1, len(chapters) + 1)
        ])
        cover_meta = ''
        if cover_image:
            manifest_items += '\n<item id="cover-image" href="cover.jpg" media-type="image/jpeg"/>'
            manifest_items += '\n<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>'
            cover_meta = '<meta name="cover" content="cover-image"/>'
            spine_items = f'<itemref idref="cover" linear="yes"/>\n' + spine_items
        content_opf = CONTENT_OPF_TEMPLATE.format(
            book_title=book_title,
            author=author,
            language=language,
            unique_id=unique_id,
            manifest_items=manifest_items,
            spine_items=spine_items,
            cover_meta=cover_meta
        )
        content_opf_path = os.path.join('OEBPS', 'content.opf')
        if not Path(content_opf_path).is_file():
            with open(content_opf_path, 'w', encoding='utf-8') as file:
                file.write(content_opf)

    def create_cover_page():
        cover_xhtml_path = os.path.join('OEBPS', 'cover.xhtml')
        if not Path(cover_xhtml_path).is_file():
            with open(cover_xhtml_path, 'w', encoding='utf-8') as file:
                file.write(COVER_XHTML)
        cover_image_path = os.path.join('OEBPS', 'cover.jpg')
        if not Path(cover_image_path).is_file():
            shutil.copy('cover.jpg', cover_image_path)

    def create_container_xml():
        container_xml_path = os.path.join('META-INF', 'container.xml')
        if not Path(container_xml_path).is_file():
            with open(container_xml_path, 'w', encoding='utf-8') as file:
                file.write(CONTAINER_XML)

    def create_mimetype_file():
        if not Path('mimetype').is_file():
            with open('mimetype', 'w', encoding='utf-8') as file:
                file.write('application/epub+zip')

    def create_epub_file(output_file):
        with zipfile.ZipFile(output_file, 'w') as epub:
            epub.write('mimetype', compress_type=zipfile.ZIP_STORED)
            for folder_name in ['META-INF', 'OEBPS']:
                for root, dirs, files in os.walk(folder_name):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if file_path == 'mimetype':
                            continue
                        epub_path = os.path.relpath(file_path).replace('\\', '/')
                        epub.write(file_path, arcname=epub_path, compress_type=zipfile.ZIP_DEFLATED)

    if not Path('input.txt').is_file():
        print("Error: No 'input.txt' found in folder")
        sys.exit(1)

    os.makedirs('OEBPS', exist_ok=True)
    os.makedirs('META-INF', exist_ok=True)
    create_mimetype_file()
    create_container_xml()
    create_stylesheet()
    chapters = parse_input('input.txt')
    create_chapter_files(chapters)
    if cover_image:
        create_cover_page()
    create_toc_ncx(chapters)
    create_content_opf(chapters)
    create_epub_file('output_file.epub')
    shutil.rmtree('OEBPS')
    shutil.rmtree('META-INF')
    os.remove('mimetype')
    print("EPUB creation complete: output.epub")

if __name__ == "__main__":
    create_epub()

