import zipfile
import xml.etree.ElementTree as ET
import sys

def get_docx_text(path):
    try:
        with zipfile.ZipFile(path) as docx:
            xml_content = docx.read('word/document.xml')
        tree = ET.XML(xml_content)
        WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
        
        paragraphs: list[str] = []
        for paragraph in tree.iter(WORD_NAMESPACE + 'p'):
            texts = [str(node.text) for node in paragraph.iter(WORD_NAMESPACE + 't') if node.text]
            if texts:
                paragraphs.append(''.join(texts))
        return '\n'.join(paragraphs)
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    text = get_docx_text(sys.argv[1])
    with open('docx_output.txt', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Done")
