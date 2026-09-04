import sys
import zipfile
from lxml import etree


def extract_comments(docx_path):
    try:
        with zipfile.ZipFile(docx_path, 'r') as z:
            names = z.namelist()

            if 'word/comments.xml' not in names:
                print('NO_COMMENTS')
                return

            # Parse comments.xml
            comments_xml  = z.read('word/comments.xml')
            comments_tree = etree.fromstring(comments_xml)
            WNS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

            comments = {}
            for c in comments_tree.findall(f'{WNS}comment'):
                cid    = c.get(f'{WNS}id')
                author = c.get(f'{WNS}author', 'Unknown')
                date   = (c.get(f'{WNS}date') or '')[:10]
                text   = ''.join(t.text or '' for t in c.findall(f'.//{WNS}t'))
                comments[cid] = {'author': author, 'date': date, 'text': text}

            if not comments:
                print('NO_COMMENTS')
                return

            # Parse document.xml to collect anchored text
            doc_xml  = z.read('word/document.xml')
            doc_tree = etree.fromstring(doc_xml)

            anchors = {cid: [] for cid in comments}
            inside  = {}

            def walk(node):
                for child in node:
                    tag     = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    cid_val = child.get(f'{WNS}id')
                    if tag == 'commentRangeStart' and cid_val in anchors:
                        inside[cid_val] = True
                    elif tag == 'commentRangeEnd':
                        inside.pop(cid_val, None)
                    elif tag == 't':
                        txt = child.text or ''
                        for cid in list(inside):
                            anchors[cid].append(txt)
                    walk(child)

            walk(doc_tree)

            anchor_texts = {cid: ''.join(v).strip() for cid, v in anchors.items()}

            print(f'Found {len(comments)} comment(s):\n')
            for i, (cid, c) in enumerate(comments.items()):
                anchor = anchor_texts.get(cid, '(no anchor text found)')
                print(f'Comment #{i}  |  {c["author"]}  |  {c["date"]}')
                print(f'  Anchored to: "{anchor}"')
                print(f'  Comment:     {c["text"]}')
                print()

    except FileNotFoundError:
        print(f'ERROR: File not found: {docx_path}')
    except zipfile.BadZipFile:
        print(f'ERROR: Not a valid .docx file: {docx_path}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python3 extract_comments.py <path_to_docx>')
        sys.exit(1)
    extract_comments(sys.argv[1])
