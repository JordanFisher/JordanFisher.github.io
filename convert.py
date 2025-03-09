def convert_doc_to_text(doc: dict) -> str:
    """Takes a Google Doc dict and converts it to a plain string, with no markup.
    
    Args:
        doc (dict): The Google Doc to convert
        
    Returns:
        str: The Google Doc as a plain string
    """
    try:
        content = ''
        
        for elem in doc['body']['content']:
            if 'paragraph' in elem:
                for para_elem in elem.get('paragraph').get('elements'):
                    if 'textRun' in para_elem:
                        content += para_elem.get('textRun').get('content')
        
        return content
    except KeyError as e:
        print(f"Error converting document to text:")
        print(f"Document: {doc}")
        print()
        print("...")
        print()
        raise e
    
def convert_doc_to_html(doc: dict) -> str:
    """Takes a Google Doc dict and converts it to an HTML string.
    
    Args:
        doc (dict): The Google Doc to convert
        
    Returns:
        str: The Google Doc as an HTML string
    """
    try:
        content = ''
        
        for elem in doc['body']['content']:
            if 'paragraph' in elem:
                content += '<p>'
                for para_elem in elem.get('paragraph').get('elements'):
                    if 'textRun' in para_elem:
                        content += para_elem.get('textRun').get('content')
                content += '</p>'
        
        return content
    except KeyError as e:
        print(f"Error converting document to HTML:")
        print(f"Document: {doc}")
        print()
        print("...")
        print()
        raise e


if __name__ == '__main__':
    import json
    import os
    from typing import List
    
    with open('fetched_docs/implicit_guardrails.json') as f:
        doc = json.load(f)
    
    txt = convert_doc_to_text(doc)
    os.makedirs('test_output', exist_ok=True)
    with open('test_output/implicit_guardrails.txt', 'w') as f:
        f.write(txt)
    
    html = convert_doc_to_html(doc)
    with open('test_output/implicit_guardrails.html', 'w') as f:
        f.write(html)
    
    print(txt)
    print()
    print(html)
    print()
    print("Done.")