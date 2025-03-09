import functools
from typing import Optional, Dict, Tuple, List, Any
import re
from bs4 import BeautifulSoup

# Global service for document fetching, to be set by the application
_docs_service = None

def set_docs_service(service):
    """Set the global docs service for document fetching.
    
    Args:
        service: The Google Docs API service instance
    """
    global _docs_service
    _docs_service = service

@functools.lru_cache(maxsize=128)
def fetch_gdoc(doc_id: str) -> Optional[Dict]:
    """Fetches a Google Doc by its ID.
    
    Args:
        doc_id (str): The ID of the document to fetch
        
    Returns:
        dict: The document represented as a dictionary, or None if fetch failed
    """
    if not _docs_service:
        print("Warning: Docs service not initialized. Cannot fetch document.")
        return None
        
    try:
        document = _docs_service.documents().get(documentId=doc_id).execute()
        return document
    except Exception as e:
        print(f"Error fetching document {doc_id}: {str(e)}")
        return None

def extract_doc_id(url: str) -> Optional[str]:
    """Extracts the document ID from a Google Docs URL.
    
    Args:
        url (str): The Google Docs URL
        
    Returns:
        str: The document ID or None if extraction failed
    """
    # Handle different URL formats
    if '/d/' in url:
        doc_id = url.split('/d/')[1].split('/')[0]
        return doc_id
    elif 'id=' in url:
        doc_id = url.split('id=')[1].split('&')[0]
        return doc_id
    return None

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

def get_gdoc_url_and_id(element: Dict) -> Tuple[Optional[str], Optional[str]]:
    """Extract Google Doc URL and ID from a rich link element.
    
    Args:
        element (dict): Element that might contain a rich link
        
    Returns:
        tuple: (url, doc_id) or (None, None) if no Google Doc link is found
    """
    if 'richLink' in element:
        rich_link = element.get('richLink', {})
        link_props = rich_link.get('richLinkProperties', {})
        url = link_props.get('uri')
        
        if url and 'docs.google.com/document' in url:
            doc_id = extract_doc_id(url)
            if doc_id:
                return url, doc_id
    
    return None, None

def convert_doc_to_html(doc_id: str) -> tuple[str, str, str]:
    """Takes a Google Doc ID, fetches it, and converts it to an HTML string with inlined links.
    Also extracts the description enclosed in [[[ and ]]] markers.
    
    Args:
        doc_id (str): The ID of the Google Doc to convert
        
    Returns:
        tuple: (title, description, html_content)
            - title (str): The document title
            - description (str): The extracted description
            - html_content (str): The Google Doc as an HTML string with the title already included and links inlined
    """
    # Fetch the document
    doc = fetch_gdoc(doc_id)
    if not doc:
        return "", "", ""
        
    # Convert the document to HTML
    title, description, html_content = _convert_doc_to_html(doc)
    
    # Process links in the HTML
    processed_html = inline_links(html_content)
    
    return title, description, processed_html

def _convert_doc_to_html(doc: dict) -> tuple[str, str, str]:
    """Internal function that converts a Google Doc dict to HTML without link inlining.
    
    Args:
        doc (dict): The Google Doc to convert
        
    Returns:
        tuple: (title, description, html_content)
    """
    try:
        content = ''
        title = ''
        if 'title' in doc:
            title = doc['title']
            # Don't add the title to the HTML content - it should be part of the document content
            # and we'll use the first H1 tag as the title in the index
        
        # Track the current list nesting level to properly manage list tags
        current_list_level = -1
        
        # For extracting description enclosed in [[[ and ]]]
        description = ""
        in_description = False
        description_paragraphs = []
        
        # For tracking consecutive empty paragraphs
        consecutive_empty_paragraphs = 0
        
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
                
                # Handle consecutive empty paragraphs
                if is_empty_paragraph and not in_description:
                    consecutive_empty_paragraphs += 1
                    continue
                else:
                    # Add <br> tags for consecutive empty paragraphs (n-1 of them)
                    if consecutive_empty_paragraphs > 1 and current_list_level < 0:
                        for i in range(consecutive_empty_paragraphs - 1):
                            content += '<br>\n'
                    consecutive_empty_paragraphs = 0
                
                # Skip processing if we're still in the description
                if in_description:
                    continue
                
                # Check if this is a heading or title
                if named_style_type == 'TITLE':
                    # Close any open lists before starting a heading
                    if current_list_level >= 0:
                        # Close all nested lists
                        for i in range(current_list_level, -1, -1):
                            content += '  ' * i + '</ul>\n'
                        current_list_level = -1
                    
                    content += '<h1 class="title-header">'
                    tag_close = '</h1>\n'
                elif named_style_type == 'SUBTITLE':
                    # Close any open lists before starting a heading
                    if current_list_level >= 0:
                        # Close all nested lists
                        for i in range(current_list_level, -1, -1):
                            content += '  ' * i + '</ul>\n'
                        current_list_level = -1
                    
                    content += '<h2 class="subtitle-header">'
                    tag_close = '</h2>\n'
                elif named_style_type == 'HEADING_1':
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
                    elif 'richLink' in para_elem:
                        # Process rich links (e.g., links to other Google Docs)
                        rich_link = para_elem.get('richLink', {})
                        link_props = rich_link.get('richLinkProperties', {})
                        url = link_props.get('uri', '')
                        title = link_props.get('title', url)
                        
                        # Create an HTML link
                        if url:
                            para_content += f'<a href="{url}">{title}</a>'
                
                # Skip empty paragraphs
                if para_content.strip() == '':
                    continue
                
                content += para_content + tag_close
            
            # Add support for other element types as needed (tables, images, etc.)
        
        # Close any remaining open lists at the end of the document
        if current_list_level >= 0:
            for i in range(current_list_level, -1, -1):
                content += '  ' * i + '</ul>\n'
                
        # Handle any trailing empty paragraphs
        if consecutive_empty_paragraphs > 1:
            for i in range(consecutive_empty_paragraphs - 1):
                content += '<br>\n'
        
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


def inline_links(html_content: str) -> str:
    """Process Google Doc links in HTML content.
    
    This function handles two types of links:
    1. Links in headers: Replace directly with the content of the linked document
    2. Links in body: Replace with a link to the anchor in the post
    
    Args:
        html_content (str): HTML content to process
    
    Returns:
        str: HTML content with links processed
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # First pass: Find and replace links in headers
    for heading in soup.find_all(['h1', 'h2', 'h3']):
        links = heading.find_all('a')
        for link in links:
            href = link.get('href')
            if href and 'docs.google.com/document' in href:
                # Extract document ID from the URL
                doc_id = extract_doc_id(href)
                if doc_id:
                    # Get the linked document's content
                    _, _, linked_html = _convert_doc_to_html(fetch_gdoc(doc_id))
                    
                    # Parse the linked document's HTML
                    linked_soup = BeautifulSoup(linked_html, 'html.parser')
                    
                    # Replace the header with the linked content directly
                    # Create a parent container for all the content
                    new_parent = soup.new_tag('div')
                    
                    # Add all elements from the linked document directly
                    for element in linked_soup.contents:
                        new_parent.append(element)
                    
                    # Replace the heading with all content
                    heading.replace_with(new_parent)
                    
                    # Remove the div wrapper to directly inline the content
                    new_parent.unwrap()
    
    # Second pass: Process links in the body
    for link in soup.find_all('a'):
        # Skip links that have already been processed
        if link.parent.name in ['h1', 'h2', 'h3']:
            continue
            
        href = link.get('href')
        if href and 'docs.google.com/document' in href:
            doc_id = extract_doc_id(href)
            if doc_id:
                # Try to find a post with this content
                post_url = None
                anchor = None
                
                # Extract anchor if present
                if '#' in href:
                    anchor = href.split('#')[-1]
                
                # Look for existing post with this doc_id
                from doc_list import gdoc_urls
                for url_names, url in gdoc_urls:
                    target_doc_id = extract_doc_id(url)
                    if doc_id == target_doc_id:
                        post_url = f"{url_names[0]}.html"
                        break
                
                # Update the link
                if post_url:
                    if anchor and anchor.startswith("heading="):
                        # Extract heading reference and convert to proper anchor format
                        heading_ref = anchor.split("=")[1]
                        # Remove any non-alphanumeric characters and convert to lowercase
                        clean_anchor = re.sub(r'[^a-zA-Z0-9]', '-', heading_ref).lower()
                        link['href'] = f"{post_url}#{clean_anchor}"
                    else:
                        link['href'] = post_url
    
    return str(soup)

if __name__ == '__main__':
    import json
    import os
    from unittest.mock import MagicMock
    
    # Create a mock docs service for testing
    mock_service = MagicMock()
    set_docs_service(mock_service)
    
    # Mock the fetch_gdoc function to return test data
    original_fetch_gdoc = fetch_gdoc
    
    def mock_fetch_gdoc(doc_id):
        if doc_id == "implicit_guardrails":
            with open('fetched_docs/implicit_guardrails.json') as f:
                return json.load(f)
        elif doc_id == "12345":
            return {
                "title": "Linked Document",
                "body": {
                    "content": [
                        {
                            "paragraph": {
                                "elements": [
                                    {
                                        "textRun": {
                                            "content": "Linked Content Title\n",
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
                                            "content": "This is content from a linked document.\n",
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
        elif doc_id == "test_doc":
            return {
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
        return None
    
    # Mock extract_doc_id for testing
    original_extract_doc_id = extract_doc_id
    
    def mock_extract_doc_id(url):
        if "implicit_guardrails" in url:
            return "implicit_guardrails"
        elif "12345" in url:
            return "12345"
        elif "67890" in url:
            return "67890"
        return None
    
    # Replace with mocks for testing
    fetch_gdoc = mock_fetch_gdoc
    extract_doc_id = mock_extract_doc_id
    
    # Test with implicit_guardrails
    print("Testing with implicit_guardrails:")
    doc = fetch_gdoc("implicit_guardrails")
    txt = convert_doc_to_text(doc)
    
    os.makedirs('test_output', exist_ok=True)
    with open('test_output/implicit_guardrails.txt', 'w') as f:
        f.write(txt)
    
    title, description, html = _convert_doc_to_html(doc)
    with open('test_output/implicit_guardrails.html', 'w') as f:
        f.write(html)
    
    print(f"Title: {title}")
    print(f"Description: {description}")
    print()
    print(f"HTML Content (first 500 chars): {html[:500]}...")
    print()
    
    # Test with a document that uses the [[[ ]]] marker in its content
    print("\nTest document with [[[ and ]]] markers:")
    doc = fetch_gdoc("test_doc")
    title, description, html = _convert_doc_to_html(doc)
    print(f"Title: {title}")
    print(f"Description: {description}")
    print(f"HTML Content: {html}")
    print()
    
    # Test with a document that uses TITLE style
    print("\nTest document with TITLE style:")
    title_doc = {
        "title": "Document with Title Style",
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "This is a title styled text\n",
                                    "textStyle": {}
                                }
                            }
                        ],
                        "paragraphStyle": {
                            "namedStyleType": "TITLE"
                        }
                    }
                },
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "This is a subtitle styled text\n",
                                    "textStyle": {}
                                }
                            }
                        ],
                        "paragraphStyle": {
                            "namedStyleType": "SUBTITLE"
                        }
                    }
                },
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "This is regular content in the body.\n",
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
    _, _, title_html = _convert_doc_to_html(title_doc)
    print(f"HTML Content: {title_html}")
    print()
    
    # Test inline_links function
    print("\nTesting inline_links function:")
    
    # Mock document with links
    mock_html = """
    <h1>Document with Links</h1>
    <h2>Heading with <a href="https://docs.google.com/document/d/12345">Link to Doc</a></h2>
    <p>This is a paragraph with a <a href="https://docs.google.com/document/d/67890#heading=h.abc123">link to another doc with anchor</a>.</p>
    <p>This is a paragraph with a <a href="https://docs.google.com/document/d/67890">link to another doc</a>.</p>
    """
    
    # Mock gdoc_urls for testing
    import sys
    from doc_list import gdoc_urls as original_gdoc_urls
    sys.modules['doc_list'].gdoc_urls = [(["test_doc_67890"], "https://docs.google.com/document/d/67890")]
    
    # Process the HTML
    processed_html = inline_links(mock_html)
    
    # Restore original gdoc_urls
    sys.modules['doc_list'].gdoc_urls = original_gdoc_urls
    
    print("Original HTML:")
    print(mock_html)
    print("\nProcessed HTML:")
    print(processed_html)
    print()
    
    # Restore original functions
    fetch_gdoc = original_fetch_gdoc
    extract_doc_id = original_extract_doc_id
    
    print("Done.")