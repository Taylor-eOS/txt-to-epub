import os
import json
from ebooklib import epub
from bs4 import BeautifulSoup

def create_epub(input_path, cover_path='cover.jpg'):
    with open("metadata.json", "r", encoding="utf-8") as meta_file:
        metadata = json.load(meta_file)

    title = metadata.get("title", "Untitled Book")
    author = metadata.get("author", "Unknown Author")
    identifier = metadata.get("identifier", "0012345678900")
    language = metadata.get("language", "en")
    css_content = metadata.get("css", "").strip()
    if not css_content:
        css_content = '''
body { font-family: serif; line-height: 1.3; margin: 0 !important; padding: 0 !important; }
h1 { font-size: 1.3em; margin: 0.3em 0; font-weight: bold; }
h2 { font-size: 1.15em; margin: 0.2em 0; font-weight: bold; }
h3 { font-size: 1em; margin: 0.1em 0; font-weight: bold; }
p { margin: 0 !important; }
blockquote { margin: 0 0 0 1em !important; padding-left: 0.5em; border-left: 1px solid #ddd; }
.footnote { font-size: 0.85em !important; color: #666; }
.footnotes { margin-top: 1em; font-size: smaller !important; color: #666; }
'''.strip()

    book = epub.EpubBook()
    book.set_identifier(identifier)
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)

    # Add CSS
    css = epub.EpubItem(uid="style_base", file_name="style/base.css", media_type="text/css", content=css_content)
    book.add_item(css)

    if os.path.exists(cover_path):
        with open(cover_path, "rb") as cover_file:
            book.set_cover("cover.jpg", cover_file.read())

    chapters = []
    toc_structure = []
    current_chapter = None
    current_footers = []
    current_header_text = None
    current_header_page = None
    current_header_tag = None

    def create_chapter(chapter_title):
        chapter = epub.EpubHtml(title=chapter_title[:50], file_name=f"chap_{len(chapters)+1}.xhtml", lang=language)
        soup = BeautifulSoup('<html><head></head><body></body></html>', 'html.parser')
        
        # Add title
        title_tag = soup.new_tag('title')
        title_tag.string = chapter_title
        soup.head.append(title_tag)
        
        # Link CSS
        link_tag = soup.new_tag('link', rel='stylesheet', href='style/base.css', type='text/css')
        soup.head.append(link_tag)
        
        return chapter, soup

    def finalize_chapter():
        nonlocal current_chapter, current_footers
        if current_chapter:
            chapter, soup = current_chapter
            if current_footers:
                footnotes_div = soup.new_tag('div', **{"class": "footnotes"})
                for footer in current_footers:
                    footnote_div = soup.new_tag('div', **{"class": "footnote"})
                    footnote_div.append(footer)  # Append parsed HTML
                    footnotes_div.append(footnote_div)
                if soup.body:
                    soup.body.append(footnotes_div)
                current_footers.clear()
            chapter.content = str(soup)
            chapters.append(chapter)
            book.add_item(chapter)
    with open(input_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            label = entry.get("label", "").lower()
            text = entry.get("text", "")
            page = entry.get("page", 0)
            if label == 'h1':
                if current_header_page == page and current_header_text is not None and current_chapter is not None:
                    current_header_text += " " + text
                    if current_header_tag:
                        current_header_tag.string = current_header_text
                    current_chapter[0].title = current_header_text[:50]
                    if current_chapter[1].head.title:
                        current_chapter[1].head.title.string = current_header_text[:50]
                else:
                    finalize_chapter()
                    chapter, soup = create_chapter(text)
                    current_chapter = (chapter, soup)
                    toc_structure.append((chapter, []))
                    current_header_tag = soup.new_tag('h1')
                    current_header_tag.string = text
                    if soup.body:
                        soup.body.append(current_header_tag)
                    current_header_text = text
                    current_header_page = page
            elif label == 'body' and current_chapter:
                _, soup = current_chapter
                p_tag = soup.new_tag('p')
                parsed_text = BeautifulSoup(text, 'html.parser')  # Parse the text as HTML
                p_tag.append(parsed_text)  # Append the parsed HTML
                if soup.body:
                    soup.body.append(p_tag)
                current_header_text = None
                current_header_page = None
            elif label == 'blockquote' and current_chapter:
                _, soup = current_chapter
                blockquote_tag = soup.new_tag('blockquote')
                parsed_text = BeautifulSoup(text, 'html.parser')  # Parse the text as HTML
                blockquote_tag.append(parsed_text)  # Append the parsed HTML
                if soup.body:
                    soup.body.append(blockquote_tag)
                current_header_text = None
                current_header_page = None
            elif label == 'footer' and current_chapter:
                parsed_text = BeautifulSoup(text, 'html.parser')  # Parse the text as HTML
                current_footers.append(parsed_text)  # Append the parsed HTML
                current_header_text = None
                current_header_page = None

            else:
                current_header_text = None
                current_header_page = None
    finalize_chapter()
    book.toc = tuple((epub.Section(chap.title, chap.file_name), []) for chap, _ in toc_structure)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters
    output_path = f"{title}.epub"
    epub.write_epub(output_path, book, {})
    print(f"Created EPUB: {output_path}")

create_epub('input_pre.json', 'cover.jpg')
