import json
from ebooklib import epub
from bs4 import BeautifulSoup
import os

def create_epub_from_textfile(input_path, metadata_path, cover_path='cover.jpg'):
    #Load metadata
    with open(metadata_path, "r") as meta_file:
        metadata = json.load(meta_file)
    title = metadata.get("title", "Untitled Book")
    author = metadata.get("author", "Unknown Author")
    identifier = metadata.get("identifier", "0012345678900")
    language = metadata.get("language", "en")
    output_path = f"{title}.epub"
    #Initialize EPUB book
    book = epub.EpubBook()
    book.set_identifier(identifier)
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)
    css = epub.EpubItem(
        uid="style_base",
        file_name="style/base.css",
        media_type="text/css",
        content='''
            body { 
                font-family: serif;
                line-height: 1.3;
                margin: 0 !important;
                padding: 0 !important;
            }
            h1 { font-size: 1.3em; margin: 0.3em 0; font-weight: bold; }
            h2 { font-size: 1.15em; margin: 0.2em 0; font-weight: bold; }
            h3 { font-size: 1em; margin: 0.1em 0; font-weight: bold; }
            p { margin: 0 !important; }
            blockquote {
                margin: 0 0 0 1em !important;
                padding-left: 0.5em;
                border-left: 1px solid #ddd;
            }
            .footnote { font-size: 0.85em; color: #666; }
        '''
    )
    book.add_item(css)
    if os.path.exists(cover_path):
        with open(cover_path, "rb") as cover_file:
            book.set_cover("cover.jpg", cover_file.read())
    #Parse input content
    with open(input_path, "r") as file:
        soup = BeautifulSoup(file.read(), "html.parser")
    chapters = []
    toc_structure = []
    current_chapter = None
    current_h2 = None
    footnote_entries = []

    def create_chapter(title):
        chapter = epub.EpubHtml(
            title=title[:50],
            file_name=f"chap_{len(chapters)+1}.xhtml",
            lang=language
        )
        chapter.add_item(css)
        chapter.content = '<body>'
        return chapter

    def finalize_chapter():
        nonlocal current_chapter, footnote_entries
        if current_chapter:
            if footnote_entries:
                current_chapter.content += '<div class="footnotes">'
                current_chapter.content += ''.join(footnote_entries)
                current_chapter.content += '</div>'
                footnote_entries = []
            current_chapter.content += '</body>'
            chapters.append(current_chapter)
            book.add_item(current_chapter)
    #Process elements
    for element in soup.find_all(True):
        if element.name == 'h1':
            finalize_chapter()
            current_chapter = create_chapter(element.get_text())
            toc_structure.append((current_chapter, []))
            current_chapter.content += " " + str(element)
        elif element.name == 'h2' and current_chapter:
            h2_id = f"sec_{len(toc_structure[-1][1])}"
            element['id'] = h2_id
            current_h2 = (
                epub.Section(element.get_text(), f"{current_chapter.file_name}#{h2_id}"),
                []
            )
            toc_structure[-1][1].append(current_h2)
            current_chapter.content += " " + str(element)
        elif element.name == 'h3' and current_chapter:
            if not toc_structure[-1][1]:
                #Create dummy H2 if missing
                h2_id = "sec_0"
                dummy_h2 = epub.Section("Section", f"{current_chapter.file_name}#{h2_id}")
                current_h2 = (dummy_h2, [])
                toc_structure[-1][1].append(current_h2)
            h3_id = f"subsec_{len(current_h2[1])}"
            element['id'] = h3_id
            current_h2[1].append(
                epub.Link(
                    f"{current_chapter.file_name}#{h3_id}",
                    element.get_text(),
                    f"subsec_{len(current_h2[1])}"
                )
            )
            current_chapter.content += " " + str(element)
        elif element.name == 'footer':
            footnote_entries.append(f'<div class="footnote">{element.get_text()}</div>')
        elif current_chapter:
            if element.name == 'bodyquote':
                current_chapter.content += f'<blockquote>{element.get_text()}</blockquote>'
            else:
                current_chapter.content += " " + str(element)
    finalize_chapter()
    #Build hierarchical TOC
    book.toc = tuple(
        (
            epub.Section(chap.title, chap.file_name),
            [
                (
                    h2_section,
                    h3_links
                ) for h2_section, h3_links in h2_entries
            ]
        ) for chap, h2_entries in toc_structure
    )
    book.add_item(epub.EpubNcx())
    nav = epub.EpubNav()
    nav.add_item(css)
    book.add_item(nav)
    book.spine = ['nav'] + chapters
    #Generate EPUB
    epub.write_epub(output_path, book, {})
    print(f"Created EPUB: {output_path}")

create_epub_from_textfile('input_pre.txt', 'metadata.json', 'cover.jpg')

