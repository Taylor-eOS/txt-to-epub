import os
import zipfile
import uuid
import re
from pathlib import Path
from epub_strings import (
    STYLESHEET_CONTENT,
    CONTAINER_XML,
    COVER_XHTML,
    NCX_TEMPLATE,
    CONTENT_OPF_TEMPLATE,
    XHTML_TEMPLATE
)
from utils import continues_block

def create_epub():
    book_title = input("Enter the book title: ").strip()
    author = input("Enter the author name: ").strip()
    language = input("Enter the language (default 'en'): ").strip() or "en"
    cover_image = 'cover.jpg' if Path('cover.jpg').is_file() else None
    unique_id = str(uuid.uuid4())
    epub_filename = f"{'_'.join(book_title.split())}.epub"

    def parse_input(txt_file):
        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        chapters = []
        chapter_stack = []
        current_chapter = {'title': None, 'body': [], 'footnotes': [], 'quotes': [], 'subchapters': []}
        current_tag = None

        for line in lines:
            line = line.strip()
            if line.startswith('<h1>'):
                if current_chapter['title']:
                    if chapter_stack:
                        chapter_stack[-1]['subchapters'].append(current_chapter)
                    else:
                        chapters.append(current_chapter)
                    current_chapter = {'title': None, 'body': [], 'footnotes': [], 'quotes': [], 'subchapters': []}
                current_chapter['title'] = line[4:]
                current_tag = 'h1'
            elif line.startswith('</h1>'):
                current_tag = None
            elif line.startswith('<body>'):
                current_tag = 'body'
                body_content = line[6:]
                if body_content:
                    current_chapter['body'].append(body_content)
            elif line.startswith('</body>'):
                current_tag = None
            elif line.startswith('<footer>'):
                current_tag = 'footer'
                footer_content = line[8:]
                if footer_content:
                    current_chapter['footnotes'].append(footer_content)
            elif line.startswith('</footer>'):
                current_tag = None
            elif line.startswith('<blockquote>'):
                current_tag = 'blockquote'
                quote_content = line[11:]
                if quote_content:
                    current_chapter['quotes'].append(quote_content)
            elif line.startswith('</blockquote>'):
                current_tag = None
            else:
                if current_tag == 'body':
                    current_chapter['body'].append(line)
                elif current_tag == 'footer':
                    current_chapter['footnotes'].append(line)
                elif current_tag == 'blockquote':
                    current_chapter['quotes'].append(line)

        if current_chapter['title']:
            if chapter_stack:
                chapter_stack[-1]['subchapters'].append(current_chapter)
            else:
                chapters.append(current_chapter)

        return chapters

    def create_stylesheet():
        with open(os.path.join('OEBPS', 'stylesheet.css'), 'w', encoding='utf-8') as file:
            file.write(STYLESHEET_CONTENT)

    def create_chapter_files(chapters):
        def recurse_chapters(chapters, parent_id=""):
            for i, chapter in enumerate(chapters, start=1):
                chapter_id = f"{parent_id}{i}"
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
                filename = f"chapter{chapter_id}.xhtml"
                with open(os.path.join('OEBPS', filename), 'w', encoding='utf-8') as file:
                    file.write(xhtml_content)
                if chapter['subchapters']:
                    recurse_chapters(chapter['subchapters'], parent_id=f"{chapter_id}-")

        recurse_chapters(chapters)

    def create_toc_ncx(chapters, parent_id=""):
        nav_points = ""
        for i, chapter in enumerate(chapters, start=1):
            nav_id = f"{parent_id}navPoint-{i}" if parent_id else f"navPoint-{i}"
            play_order = f"{parent_id}{i}" if parent_id else f"{i}"
            content_src = f"chapter{parent_id}{i}.xhtml" if parent_id else f"chapter{i}.xhtml"
            nav_points += f'''<navPoint id="{nav_id}" playOrder="{play_order}">
      <navLabel>
        <text>{chapter["title"]}</text>
      </navLabel>
      <content src="{content_src}"/>
    '''
            if chapter['subchapters']:
                nav_points += create_toc_ncx(chapter['subchapters'], parent_id=f"{i}-")
            nav_points += '</navPoint>\n'
        return nav_points

    def create_content_opf(chapters):
        def recurse_manifest(chapters, parent_id=""):
            manifest = ""
            for i, chapter in enumerate(chapters, start=1):
                chapter_id = f"{parent_id}{i}"
                manifest += f'<item id="chapter{chapter_id}" href="chapter{chapter_id}.xhtml" media-type="application/xhtml+xml"/>\n'
                if chapter['subchapters']:
                    manifest += recurse_manifest(chapter['subchapters'], parent_id=f"{chapter_id}-")
            return manifest

        manifest_items = recurse_manifest(chapters)
        spine_items = ""
        def recurse_spine(chapters, parent_id=""):
            spine = ""
            for i, chapter in enumerate(chapters, start=1):
                chapter_id = f"{parent_id}{i}"
                spine += f'<itemref idref="chapter{chapter_id}"/>\n'
                if chapter['subchapters']:
                    spine += recurse_spine(chapter['subchapters'], parent_id=f"{chapter_id}-")
            return spine

        spine_items = recurse_spine(chapters)
        cover_manifest = ''
        cover_meta = ''
        if cover_image:
            manifest_items += f'<item id="cover" href="cover.jpg" media-type="image/jpeg"/>\n'
            manifest_items += '<item id="cover-page" href="cover.xhtml" media-type="application/xhtml+xml"/>\n'
            spine_items = f'<itemref idref="cover-page"/>\n' + spine_items
            cover_meta = '<meta name="cover" content="cover"/>'
        content_opf = CONTENT_OPF_TEMPLATE.format(
            book_title=book_title,
            author=author,
            language=language,
            unique_id=unique_id,
            manifest_items=manifest_items.strip(),
            spine_items=spine_items.strip(),
            cover_manifest=cover_meta
        )
        with open(os.path.join('OEBPS', 'content.opf'), 'w', encoding='utf-8') as file:
            file.write(content_opf)

    def create_cover_page():
        with open(os.path.join('OEBPS', 'cover.xhtml'), 'w', encoding='utf-8') as file:
            file.write(COVER_XHTML)

    def create_container_xml():
        with open(os.path.join('META-INF', 'container.xml'), 'w', encoding='utf-8') as file:
            file.write(CONTAINER_XML)

    def create_mimetype_file():
        with open('mimetype', 'w', encoding='utf-8') as file:
            file.write('application/epub+zip')

    def create_epub_file(output_file):
        with zipfile.ZipFile(output_file, 'w') as epub:
            epub.write('mimetype', compress_type=zipfile.ZIP_STORED)
            for folder_name in ['META-INF', 'OEBPS']:
                for root, dirs, files in os.walk(folder_name):
                    for file in files:
                        file_path = os.path.join(root, file)
                        epub_path = os.path.relpath(file_path).replace('\\', '/')
                        epub.write(file_path, arcname=epub_path, compress_type=zipfile.ZIP_DEFLATED)
            if cover_image:
                epub.write('cover.jpg', arcname='OEBPS/cover.jpg', compress_type=zipfile.ZIP_DEFLATED)

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
    create_epub_file(epub_filename)
    print(f"EPUB creation complete: {epub_filename}")

create_epub()

