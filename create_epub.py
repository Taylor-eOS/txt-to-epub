import os
import zipfile
import uuid
import re
import sys
import shutil
from pathlib import Path
from utils import continues_block
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
        chapter_data = {'title': None, 'body': [], 'footnotes': [], 'quotes': []}
        current_tag = None
        for line in lines:
            line = line.strip()
            if line.startswith('<h1>'):
                if chapter_data['title']:
                    chapters.append(chapter_data)
                    chapter_data = {'title': None, 'body': [], 'footnotes': [], 'quotes': []}
                chapter_data['title'] = line[4:].rstrip('</h1>')
                current_tag = 'h1'
            elif line.startswith('<body>'):
                current_tag = 'body'
                body_content = line[6:].rstrip('</body>')
                if body_content:
                    chapter_data['body'].append(body_content)
            elif line.startswith('<footer>'):
                current_tag = 'footer'
                footer_content = line[8:].rstrip('</footer>')
                if footer_content:
                    chapter_data['footnotes'].append(footer_content)
            elif line.startswith('<blockquote>'):
                current_tag = 'blockquote'
                quote_content = line[11:].rstrip('</blockquote>')
                if quote_content:
                    chapter_data['quotes'].append(quote_content)
            else:
                if current_tag == 'body':
                    chapter_data['body'].append(line)
                elif current_tag == 'footer':
                    chapter_data['footnotes'].append(line)
                elif current_tag == 'blockquote':
                    chapter_data['quotes'].append(line)
        if chapter_data['title']:
            chapters.append(chapter_data)
        return chapters

    def create_stylesheet():
        stylesheet_path = os.path.join('OEBPS', 'stylesheet.css')
        if not Path(stylesheet_path).is_file():
            with open(stylesheet_path, 'w', encoding='utf-8') as file:
                file.write(STYLESHEET_CONTENT.replace("margin: 0;", "margin: 0 !important;")
                                              .replace("padding: 1em;", "padding: 0 !important;"))

    def create_chapter_files(chapters):
        for i, chapter in enumerate(chapters, start=1):
            content = ""
            previous_sentence = ""
            for block in chapter['body']:
                sentences = re.split(r'(?<=[\.!\?])\s+', block)
                for sentence in sentences:
                    status = continues_block(previous_sentence, sentence)
                    if status in ['continues_word', 'continues_sentence']:
                        if content.endswith('</p>\n'):
                            content = content[:-5] + ' ' + sentence + '</p>\n'
                        else:
                            content += sentence + ' '
                    else:
                        content += f'<p>{sentence}</p>\n'
                    previous_sentence = sentence
            for quote in chapter['quotes']:
                content += f'<blockquote>{quote}</blockquote>\n'
            if chapter['footnotes']:
                content += '<div class="footer">\n'
                for footnote in chapter['footnotes']:
                    content += f'<p>{footnote}</p>\n'
                content += '</div>\n'
            xhtml_content = XHTML_TEMPLATE.format(title=chapter["title"], content=content)
            filename = f"chapter{i}.xhtml"
            chapter_path = os.path.join('OEBPS', filename)
            if not Path(chapter_path).is_file():
                with open(chapter_path, 'w', encoding='utf-8') as file:
                    file.write(xhtml_content)

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
    create_epub_file('output.epub')
    print("EPUB creation complete: output.epub")

if __name__ == "__main__":
    create_epub()

