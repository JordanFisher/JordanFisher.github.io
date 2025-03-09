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
    
def convert_doc_to_html(doc: dict) -> tuple[str, str, str]:
    """Takes a Google Doc dict and converts it to an HTML string.
    Also extracts the description enclosed in [[[ and ]]] markers.
    
    Args:
        doc (dict): The Google Doc to convert
        
    Returns:
        tuple: (title, description, html_content)
            - title (str): The document title
            - description (str): The extracted description
            - html_content (str): The Google Doc as an HTML string
    """
    try:
        content = ''
        title = ''
        if 'title' in doc:
            title = doc['title']
            content += f'<h1>{title}</h1>\n'
        
        # Track the current list nesting level to properly manage list tags
        current_list_level = -1
        
        # For extracting description enclosed in [[[ and ]]]
        description = ""
        in_description = False
        description_paragraphs = []
        
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
                
                # Extract the raw text from the paragraph for checking description markers
                raw_text = ''
                for para_elem in paragraph.get('elements', []):
                    if 'textRun' in para_elem:
                        text_content = para_elem.get('textRun', {}).get('content', '')
                        if text_content.endswith('\n'):
                            text_content = text_content[:-1]
                        raw_text += text_content
                
                # Check for description markers - handling both single-paragraph and multi-paragraph cases
                if raw_text.lstrip().startswith('[[[') and raw_text.rstrip().endswith(']]]'):
                    # Single paragraph description
                    in_description = False  # No need to continue in description mode
                    # Remove the markers from a single-paragraph description
                    desc_text = raw_text.replace('[[[', '', 1)
                    desc_text = desc_text.rsplit(']]]', 1)[0].strip()
                    description_paragraphs.append(desc_text)
                    continue  # Skip adding this to the HTML content
                elif raw_text.lstrip().startswith('[[['):
                    in_description = True
                    # Remove the [[[ marker from the first paragraph
                    raw_text = raw_text.replace('[[[', '', 1).strip()
                    description_paragraphs.append(raw_text)
                    continue  # Skip adding this to the HTML content
                elif in_description and raw_text.rstrip().endswith(']]]'):
                    # Remove the ]]] marker from the last paragraph
                    raw_text = raw_text.rsplit(']]]', 1)[0].strip()
                    if raw_text:  # Only add if there's content after removing the marker
                        description_paragraphs.append(raw_text)
                    in_description = False
                    continue  # Skip adding this to the HTML content
                elif in_description:
                    # This is a paragraph in the middle of the description
                    description_paragraphs.append(raw_text.strip())
                    continue  # Skip adding this to the HTML content
                
                # Skip formatting for empty paragraphs but still add some space
                if is_empty_paragraph and not in_description:
                    # If we're not in a list, just add a blank line
                    if current_list_level < 0:
                        content += '<br>\n'
                    continue
                
                # Skip processing if we're still in the description
                if in_description:
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
        
        # Join the description paragraphs with paragraph breaks
        description = "<br><br>".join(description_paragraphs)
        
        return title, description, content
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
    
    # Test with implicit_guardrails.json which has the marker
    print("Testing with implicit_guardrails.json:")
    with open('fetched_docs/implicit_guardrails.json') as f:
        doc = json.load(f)
    
    txt = convert_doc_to_text(doc)
    os.makedirs('test_output', exist_ok=True)
    with open('test_output/implicit_guardrails.txt', 'w') as f:
        f.write(txt)
    
    title, description, html = convert_doc_to_html(doc)
    with open('test_output/implicit_guardrails.html', 'w') as f:
        f.write(html)
    
    print(f"Title: {title}")
    print(f"Description: {description}")
    print()
    print(f"HTML Content (first 500 chars): {html[:500]}...")
    print()
    
    # Test with a document that uses the [[[ ]]] marker in its content
    print("\nTest document with [[[ and ]]] markers:")
    test_data = {
        "title": "Test Document",
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "This is the title\n",
                                    "textStyle": {}
                                }
                            }
                        ],
                        "paragraphStyle": {
                            "namedStyleType": "HEADING_1"
                        }
                    }
                },
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "[[[This is the first paragraph of the description\n",
                                    "textStyle": {}
                                }
                            }
                        ],
                        "paragraphStyle": {
                            "namedStyleType": "NORMAL_TEXT"
                        }
                    }
                },
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "This is the second paragraph of the description]]]\n",
                                    "textStyle": {}
                                }
                            }
                        ],
                        "paragraphStyle": {
                            "namedStyleType": "NORMAL_TEXT"
                        }
                    }
                },
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "This is regular content that should be in the body.\n",
                                    "textStyle": {}
                                }
                            }
                        ],
                        "paragraphStyle": {
                            "namedStyleType": "NORMAL_TEXT"
                        }
                    }
                }
            ]
        }
    }
    
    title, description, html = convert_doc_to_html(test_data)
    print(f"Title: {title}")
    print(f"Description: {description}")
    print(f"HTML Content: {html}")
    print()
    print("Done.")