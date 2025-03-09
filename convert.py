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
        if 'title' in doc:
            content += f'<h1>{doc["title"]}</h1>\n'
        
        # Track the current list nesting level to properly manage list tags
        current_list_level = -1
        
        for elem in doc['body']['content']:
            if 'paragraph' in elem:
                paragraph = elem.get('paragraph')
                
                # Check if this is an empty paragraph with only a newline
                is_empty_paragraph = False
                if len(paragraph.get('elements', [])) == 1:
                    element = paragraph.get('elements')[0]
                    if 'textRun' in element:
                        text_content = element.get('textRun', {}).get('content', '')
                        if text_content == '\n' or text_content.strip() == '':
                            is_empty_paragraph = True
                
                # Get paragraph style
                paragraph_style = paragraph.get('paragraphStyle', {})
                named_style_type = paragraph_style.get('namedStyleType', 'NORMAL_TEXT')
                
                # Skip formatting for empty paragraphs but still add some space
                if is_empty_paragraph:
                    # If we're not in a list, just add a blank line
                    if current_list_level < 0:
                        content += '<br>\n'
                    continue
                
                # Check if this is a heading
                if named_style_type == 'HEADING_1':
                    # Close any open lists before starting a heading
                    if current_list_level >= 0:
                        # Close all nested lists
                        for i in range(current_list_level, -1, -1):
                            content += '  ' * i + '</ul>\n'
                        current_list_level = -1
                    
                    content += '<h1>'
                    tag_close = '</h1>\n'
                elif named_style_type == 'HEADING_2':
                    # Close any open lists before starting a heading
                    if current_list_level >= 0:
                        # Close all nested lists
                        for i in range(current_list_level, -1, -1):
                            content += '  ' * i + '</ul>\n'
                        current_list_level = -1
                    
                    content += '<h2>'
                    tag_close = '</h2>\n'
                elif named_style_type == 'HEADING_3':
                    # Close any open lists before starting a heading
                    if current_list_level >= 0:
                        # Close all nested lists
                        for i in range(current_list_level, -1, -1):
                            content += '  ' * i + '</ul>\n'
                        current_list_level = -1
                    
                    content += '<h3>'
                    tag_close = '</h3>\n'
                else:
                    # Check if this is a list item
                    if 'bullet' in paragraph:
                        nesting_level = paragraph['bullet'].get('nestingLevel', 0)
                        
                        # Handle list nesting
                        if nesting_level > current_list_level:
                            # Need to open new list level(s)
                            for i in range(current_list_level + 1, nesting_level + 1):
                                # Indent according to nesting level
                                content += '  ' * i + '<ul>\n'
                        elif nesting_level < current_list_level:
                            # Need to close some list levels
                            for i in range(current_list_level, nesting_level, -1):
                                content += '  ' * i + '</ul>\n'
                        
                        current_list_level = nesting_level
                        
                        # Add the list item with proper indentation
                        content += '  ' * (nesting_level + 1) + '<li>'
                        tag_close = '</li>\n'
                    else:
                        # Regular paragraph - close any open lists
                        if current_list_level >= 0:
                            # Close all nested lists
                            for i in range(current_list_level, -1, -1):
                                content += '  ' * i + '</ul>\n'
                            current_list_level = -1
                        
                        content += '<p>'
                        tag_close = '</p>\n'
                
                # Process text elements within the paragraph
                para_content = ''
                for para_elem in paragraph.get('elements', []):
                    if 'textRun' in para_elem:
                        text_run = para_elem.get('textRun', {})
                        text_content = text_run.get('content', '')
                        text_style = text_run.get('textStyle', {})
                        
                        # Strip trailing newline character, it will be handled by HTML tags
                        if text_content.endswith('\n'):
                            text_content = text_content[:-1]
                        
                        # Apply text styling
                        styled_text = text_content
                        
                        # Apply text styling in the correct order (inside out)
                        if text_style.get('strikethrough', False):
                            styled_text = f'<s>{styled_text}</s>'
                        if text_style.get('underline', False):
                            styled_text = f'<u>{styled_text}</u>'
                        if text_style.get('italic', False):
                            styled_text = f'<em>{styled_text}</em>'
                        if text_style.get('bold', False):
                            styled_text = f'<strong>{styled_text}</strong>'
                            
                        para_content += styled_text
                
                # Skip empty paragraphs
                if para_content.strip() == '':
                    continue
                
                content += para_content + tag_close
            
            # Add support for other element types as needed (tables, images, etc.)
        
        # Close any remaining open lists at the end of the document
        if current_list_level >= 0:
            for i in range(current_list_level, -1, -1):
                content += '  ' * i + '</ul>\n'
        
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