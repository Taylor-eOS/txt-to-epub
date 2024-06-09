import os
import zipfile
import uuid

def create_epub(txt_file):
    book_title = "Your Book Title"
    author = "Your Name"
    language = "en"
    unique_id = str(uuid.uuid4())

    def create_chapter_files(txt_file):
        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        chapters = []
        chapter_title = None
        chapter_content = []

        for line in lines:
            if line.startswith("Chapter: "):
                if chapter_title:
                    chapters.append((chapter_title, ''.join(chapter_content)))
                chapter_title = line.strip().replace("Chapter: ", "")
                chapter_content = []
            else:
                chapter_content.append(line)

        if chapter_title:
            chapters.append((chapter_title, ''.join(chapter_content)))

        return chapters

    def create_xhtml_file(title, content, chapter_index):
        xhtml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>{title}</title>
  <link href="stylesheet.css" rel="stylesheet" type="text/css" />
</head>
<body>
  <h1>{title}</h1>
  {content}
</body>
</html>'''
        filename = f"chapter{chapter_index}.xhtml"
        with open(os.path.join('OEBPS', filename), 'w', encoding='utf-8') as file:
            file.write(xhtml_content)

    def create_content_opf(chapters):
        manifest_items = '\n'.join([f'<item id="chapter{i}" href="chapter{i}.xhtml" media-type="application/xhtml+xml"/>' for i in range(1, len(chapters) + 1)])
        spine_items = '\n'.join([f'<itemref idref="chapter{i}"/>' for i in range(1, len(chapters) + 1)])

        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{book_title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>{language}</dc:language>
    <dc:identifier id="BookID">urn:uuid:{unique_id}</dc:identifier>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="css" href="stylesheet.css" media-type="text/css"/>
    {manifest_items}
  </manifest>
  <spine toc="ncx">
    {spine_items}
  </spine>
</package>'''

        with open(os.path.join('OEBPS', 'content.opf'), 'w', encoding='utf-8') as file:
            file.write(content_opf)

    def create_toc_ncx(chapters):
        nav_points = '\n'.join([f'''<navPoint id="navPoint-{i}" playOrder="{i}">
      <navLabel>
        <text>{title}</text>
      </navLabel>
      <content src="chapter{i}.xhtml"/>
    </navPoint>''' for i, (title, _) in enumerate(chapters, start=1)])

        toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{unique_id}"/>
    <meta name="dtb:depth" content="1"/>
  </head>
  <docTitle>
    <text>{book_title}</text>
  </docTitle>
  <navMap>
    {nav_points}
  </navMap>
</ncx>'''

        with open(os.path.join('OEBPS', 'toc.ncx'), 'w', encoding='utf-8') as file:
            file.write(toc_ncx)

    def create_stylesheet():
        stylesheet_content = '''body {
  font-family: Arial, sans-serif;
  line-height: 1.6;
  margin: 0;
  padding: 0;
}

h1, h2, h3 {
  text-align: center;
}

p {
  text-indent: 1.5em;
  margin: 0 0 1em 0;
}'''

        with open(os.path.join('OEBPS', 'stylesheet.css'), 'w', encoding='utf-8') as file:
            file.write(stylesheet_content)

    def create_container_xml():
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''

        os.makedirs('META-INF', exist_ok=True)
        with open(os.path.join('META-INF', 'container.xml'), 'w', encoding='utf-8') as file:
            file.write(container_xml)

    def create_mimetype():
        with open('mimetype', 'w', encoding='utf-8') as file:
            file.write('application/epub+zip')

    def create_epub_file(output_file):
        with zipfile.ZipFile(output_file, 'w') as epub:
            epub.write('mimetype', compress_type=zipfile.ZIP_STORED)
            for folder_name in ['META-INF', 'OEBPS']:
                for root, dirs, files in os.walk(folder_name):
                    for file in files:
                        epub.write(os.path.join(root, file))

    # Create necessary directories
    os.makedirs('OEBPS', exist_ok=True)

    # Create files
    create_mimetype()
    create_container_xml()
    chapters = create_chapter_files(txt_file)
    for i, (title, content) in enumerate(chapters, start=1):
        create_xhtml_file(title, content, i)
    create_content_opf(chapters)
    create_toc_ncx(chapters)
    create_stylesheet()

    # Create the epub file
    create_epub_file('output.epub')

# Usage
create_epub('input.txt')