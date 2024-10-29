This script takes blocks of text from an input TXT file and wraps them into EPUB. It is a lightweight tool, written by an amateur, with a chatbot. 
The script structures chapters and adds metadata and a cover image.\
The current state of the project is that it works, but doesn't nest chapters or superscript footnote references. The resulting files will be readable, but a little crude.

### How to Use `txt-to-epub`
1. **Pre-process the Text**: The input needs to be in a particular format, which can be extracted from PDF using [maual-classifier](https://github.com/Taylor-eOS/manual-classifier).

2. Before running the main script, use `pre_processing.py` to combine the blocks properly. (This was tested on particular files, and might need adaptation with some input formats.)
   ```bash
   python pre_processing.py input.txt
   ```
   This will generate a cleaned text file ready for EPUB conversion.

3. Edit `metadata.json` to contain your author and title data.

4. **Generate the EPUB**: Run `create_epub.py` to convert your cleaned text file to EPUB format. If you plae a cover image (`cover.jpg`) in the folder, it will be used.
   ```bash
   python create_epub.py cleaned_input.txt metadata.json
   ```
The script should output a properly formatted EPUB file named after the book title, that can be read on e-readers.
