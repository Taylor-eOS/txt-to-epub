import json
from ebooklib import epub
from bs4 import BeautifulSoup
import os

def create_epub_from_textfile(input_path, metadata_path, cover_path='cover.jpg'):
    # Load metadata
    with open(metadata_path, "r") as meta_file:
        metadata = json.load(meta_file)
    
    title = metadata.get("title", "Untitled Book")
    author = metadata.get("author", "Unknown Author")
    identifier = metadata.get("identifier", "id123456")
    language = metadata.get("language", "en")
    output_path = f"{title}.epub"

    # Initialize the EPUB book
    book = epub.EpubBook()
    book.set_identifier(identifier)
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)

    # Add CSS stylesheet
    style = '''
    body { margin: 0 !important; padding: 0 !important; line-height: 1.5; }
    h1 { font-size: 1.5em; margin: 0 !important; padding: 0 !important; }
    p { margin: 0 !important; padding: 0 !important; }
    blockquote { margin: 0 !important; padding: 0 !important; font-style: italic; }
    '''
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    book.add_item(nav_css)

    # Add cover image if it exists
    if os.path.exists(cover_path):
        with open(cover_path, "rb") as cover_file:
            cover_image = cover_file.read()
            book.set_cover("cover.jpg", cover_image)
    else:
        print(f"Warning: Cover image '{cover_path}' not found. EPUB will have no cover.")

    # Read and parse the input HTML content
    with open(input_path, "r") as file:
        content = file.read()
    soup = BeautifulSoup(content, "html.parser")

    chapters = []
    chapter_content = ""
    footnotes = []
    chapter_titles = []
    chapter_num = 1

    for tag in soup.find_all(True):
        if tag.name == "h1":
            if chapter_content:
                final_content = chapter_content + "".join(footnotes)
                chapter_title = chapter_titles[-1] if chapter_titles else f"Chapter {chapter_num}"
                chapter = epub.EpubHtml(title=chapter_title[:30], file_name=f"chap_{chapter_num}.xhtml", lang=language)
                chapter.content = final_content
                book.add_item(chapter)
                chapters.append(chapter)
                chapter_content = ""
                footnotes = []
                chapter_num += 1
            chapter_content += f"<h1>{tag.text}</h1>"
            chapter_titles.append(tag.text)
        elif tag.name == "body":
            chapter_content += f"<p style='display: inline;'>{tag.text}</p>"
        elif tag.name == "footer":
            footnotes.append(f"<p style='font-size: 0.8em; color: gray;'>{tag.text}</p>")
        elif tag.name == "bodyquote":
            chapter_content += f"<blockquote>{tag.text}</blockquote>"

    # Add the last chapter if exists
    if chapter_content:
        final_content = chapter_content + "".join(footnotes)
        chapter_title = chapter_titles[-1] if chapter_titles else f"Chapter {chapter_num}"
        chapter = epub.EpubHtml(title=chapter_title[:30], file_name=f"chap_{chapter_num}.xhtml", lang=language)
        chapter.content = final_content
        book.add_item(chapter)
        chapters.append(chapter)

    # Define Table of Contents and Spine
    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters

    # Optionally, add default cover page (recommended but not required)
    # cover_page = epub.EpubHtml(title='Cover', file_name='cover.xhtml', lang=language)
    # cover_page.content = f'<html><head></head><body><img src="cover.jpg" alt="Cover"/></body></html>'
    # book.add_item(cover_page)
    # book.spine.insert(1, cover_page)

    # Write the EPUB file
    epub.write_epub(output_path, book)
    print(f"EPUB '{output_path}' created successfully")

# Usage
create_epub_from_textfile('input.txt', 'metadata.json', 'cover.jpg')

