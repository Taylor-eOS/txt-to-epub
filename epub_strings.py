STYLESHEET_CONTENT = '''body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0 !important;
    padding: 0 !important;
}

h1, h2, h3 {
    text-align: center;
    font-weight: bold;
    margin: 0 !important;
    padding: 0 !important;
}

p {
    text-indent: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

blockquote {
    margin: 0 !important;
    padding: 0 !important;
    font-style: italic;
    border-left: 4px solid #ccc;
    padding-left: 1em;
}

.footer {
    font-size: 0.8em;
    color: #555;
    margin: 0 !important;
    padding: 0 !important;
}'''

CONTAINER_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''

COVER_XHTML = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Cover</title>
  <link href="stylesheet.css" rel="stylesheet" type="text/css" />
</head>
<body>
  <div style="text-align: center; padding: 5% !important;">
    <img src="cover.jpg" alt="Cover Image" style="max-width: 100%; height: auto;"/>
  </div>
</body>
</html>'''

NCX_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{unique_id}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>{book_title}</text>
  </docTitle>
  <navMap>
    {nav_points}
  </navMap>
</ncx>'''

CONTENT_OPF_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{book_title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>{language}</dc:language>
    <dc:identifier id="BookID">urn:uuid:{unique_id}</dc:identifier>
    {cover_meta}
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

XHTML_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
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

