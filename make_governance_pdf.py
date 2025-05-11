#!/usr/bin/env python3
import os
import sys
import re
import argparse
from bs4 import BeautifulSoup
import subprocess
from dataclasses import dataclass
from typing import List, Optional
import make_governance
from liberty_by_design_versions import liberty_versions, BookVersion

@dataclass
class LatexDocument:
    title: str
    content: str
    description: Optional[str] = None
    include_images: bool = False
    template_type: str = "print"  # "print" or "mobile"
    
    def to_latex(self) -> str:
        """Generate a complete LaTeX document string using template file."""
        # Select template based on template_type
        if self.template_type == "mobile":
            template_file = "mobile_template.tex"
        else:  # Default to print template
            template_file = "pocket_book_template.tex"
            
        template_path = os.path.join(os.path.dirname(__file__), "latex_templates", template_file)
        
        try:
            with open(template_path, "r") as f:
                template = f.read()
        except FileNotFoundError:
            # Throw an exception if template file is missing
            raise FileNotFoundError(f"Error: Template file {template_path} not found.")
            
        # Prepare description block with page break after
        description_block = ""
        if self.description:
            description_block = f"""
\\begin{{fancyquote}}
{self.description}
\\end{{fancyquote}}

\\clearpage
"""

        # Add the longtable and array packages
        if "\\usepackage{longtable}" not in template and "\\begin{longtable}" in self.content:
            # Find a good spot to add the package - after other package includes
            package_insert_pos = template.find("\\usepackage{mdframed}")
            if package_insert_pos != -1:
                template = template[:package_insert_pos + 21] + "\n\\usepackage{longtable}\n\\usepackage{array}" + template[package_insert_pos + 21:]
        
        # Replace placeholders in template
        latex = template.replace("$title$", self.title)
        latex = latex.replace("$main_description$", self.description or "")
        latex = latex.replace("$content$", self.content)
        
        return latex


def html_to_latex(html_path: str, include_images: bool = False) -> LatexDocument:
    """Convert HTML file to LaTeX document."""
    
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    # Fix invalid HTML structure - nested uls should be inside li tags
    html_content = html_content.replace('</li>\n<ul>', '<ul>')
    html_content = html_content.replace('</ul>\n<li>', '</ul></li>\n<li>')
    
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract content from the #story div
    story_div = soup.find('div', id='story')
    if not story_div:
        raise ValueError("Could not find #story div in HTML file")
    
    # Get title
    title = "Liberty by Design"
    
    # Get description if available
    description = None
    description_block = story_div.find('div', class_='description-block')
    if description_block:
        # Process each paragraph with formatting and join them
        description = ' '.join([process_inline_elements(p, story_div=story_div) for p in description_block.find_all('p')])
    
    # Process all elements in the HTML body
    latex_content = ""
    
    # Remove the title and description before processing content
    if description_block:
        description_block.extract()
        
    # Also remove the redundant book title (Liberty by Design) since it's already at the top
    # Find the h1 with title "Liberty by Design" or similar
    book_title = soup.find('h1', string=lambda text: text and "Liberty by Design" in text)
    if book_title:
        print("Removing redundant book title header from content...")
        book_title.extract()
        
    # First look for the table of contents div to custom format it
    toc_div = story_div.find('div', class_='table-of-contents')
    if toc_div:
        print("Found table-of-contents div, creating custom TOC...")
        # Extract the TOC div to process it separately
        toc_div.extract()
        
        # Create a custom formatted table of contents
        toc_content = """\\subsection*{\\Large Table of Contents}
\\vspace{0.5cm}

\\begin{longtable}{p{0.8\\textwidth}r}
"""

        # Extract chapter entries from the TOC div
        chapter_headings = []
        for li in toc_div.find_all('li'):
            link = li.find('a')
            if link:
                link_text = link.get_text().strip()
                heading_id = link.get('href', '').replace('#', '')
                
                # Extract chapter number if present
                if "Chapter " in link_text:
                    parts = link_text.split(":", 1)
                    if len(parts) == 2:
                        # Format as "Chapter X" (without the comma)
                        chapter_num = parts[0].strip()
                        
                        heading_text = parts[1].strip()
                        chapter_headings.append((chapter_num, heading_text, heading_id))
        
        # Generate TOC entries
        for chapter_num, heading_text, heading_id in chapter_headings:
            # Format with chapter number first, then page num, then title on a separate line.
            # Add more vertical space before each chapter entry.
            toc_content += f"""\\noalign{{\\vspace{{2em}}}}
\\nopagebreak
{{\\headingfont\\itshape {chapter_num}}} & {{\\headingfont\\itshape pg.~\\pageref{{{heading_id}}}}} \\\\[0.3cm]
\\nopagebreak
\\multicolumn{{2}}{{p{{\\textwidth}}}}{{\\Large\\headingfont\\itshape {heading_text}}} \\\\
"""
        
        # Close the TOC
        toc_content += """\\end{longtable}
\\vspace{0.5cm}
"""
        latex_content += toc_content
    
    for element in story_div.children:
        if element.name is None:  # Skip text nodes
            continue
            
        if element.name == 'h1' or element.name == 'h2':
            # Skip if this is the title (ie, if it has the same text as the book title).
            if element.get_text(strip=True).lower().strip() == "Liberty by Design".lower().strip():
                print("Skipping book title header...")
                continue

            if element.name == 'h1':
                if 'title-header' in element.get('class', []):
                    print(f"     {element} (title-header)")
                else:
                    print(f"     {element}")
            # Get the ID for label if available
            element_id = element.get('id', '')
            label_markup = f"\\phantomsection\\label{{{element_id}}}" if element_id else ""
            
            # Only add page break if it's a title header (new document being inlined)
            if 'title-header' in element.get('class', []):
                # Add spacing after page break before the title header
                # Process the header with formatting (bold, italic, strikethrough)
                
                # Check for chapter number
                chapter_number_tag = element.find('span', class_='chapter-number')
                chapter_prefix = ""
                
                if chapter_number_tag:
                    chapter_number = chapter_number_tag.get_text().strip()
                    # Remove the chapter number span from the element for regular processing
                    chapter_number_tag.extract()
                    
                    header_text = process_inline_elements(element, story_div=story_div)
                    # Format chapter number without the colon
                    chapter_number_clean = chapter_number.replace(':', '')
                    
                    latex_content += f"""\\clearpage
{label_markup}
\\vspace*{{1.5cm}}
{{\\headingfont\\itshape\\small {chapter_number_clean}}}
\\vspace{{-0.5cm}}
\\section*{{\\huge {header_text}}}
\\vspace{{0.7cm}}

"""
                else:
                    header_text = process_inline_elements(element, story_div=story_div)
                    latex_content += f"\\clearpage\n{label_markup}\n\\vspace*{{1.5cm}}\n\\section*{{\\huge {header_text}}}\n\\vspace{{0.7cm}}\n\n"
                
                # Look for a description block right after this title
                next_elem = element.find_next_sibling()
                if next_elem and next_elem.name == 'div' and 'description-block' in next_elem.get('class', []):
                    desc_text = ' '.join([process_inline_elements(p, story_div=story_div) for p in next_elem.find_all('p')])
                    latex_content += f"""\\begin{{fancyquote}}
{desc_text}
\\end{{fancyquote}}\\vspace{{1.2cm}}\n\n"""
                    # Skip this description block when we encounter it in the normal loop
                    next_elem['processed'] = True
            else:
                # Check for chapter number
                chapter_number_tag = element.find('span', class_='chapter-number')
                chapter_prefix = ""
                
                if chapter_number_tag:
                    chapter_number = chapter_number_tag.get_text().strip()
                    # Remove the chapter number span from the element for regular processing
                    chapter_number_tag.extract()
                    
                    header_text = process_inline_elements(element, story_div=story_div)
                    # Format chapter number without the colon
                    chapter_number_clean = chapter_number.replace(':', '')
                    
                    latex_content += f"""{label_markup}
{{\\headingfont\\itshape\\small {chapter_number_clean}}}
\\vspace{{-0.5cm}}
\\section*{{{header_text}}}
\\vspace{{0.5cm}}

"""
                else:
                    header_text = process_inline_elements(element, story_div=story_div)
                    latex_content += f"{label_markup}\n\\vspace{{1.1cm}}\n\\section*{{{header_text}}}\n\\vspace{{0.3cm}}\n\n"
        elif element.name == 'h2':
            # Get the ID for label if available
            element_id = element.get('id', '')
            label_markup = f"\\phantomsection\\label{{{element_id}}}" if element_id else ""
            
            header_text = process_inline_elements(element, story_div=story_div)
            latex_content += f"{label_markup}\n\\needspace{{3\\baselineskip}}\\vspace{{0.1cm}}\n\\subsection*{{{header_text}}}\n\\vspace{{0.3cm}}\n\n"
        elif element.name == 'h3':
            # Get the ID for label if available
            element_id = element.get('id', '')
            label_markup = f"\\phantomsection\\label{{{element_id}}}" if element_id else ""
            
            header_text = process_inline_elements(element, story_div=story_div)
            latex_content += f"{label_markup}\n\\needspace{{2\\baselineskip}}\n\\subsubsection*{{{header_text}}}\n\\vspace{{0.2cm}}\n\n"
        elif element.name == 'p':
            # Check if this paragraph contains an image container
            img_container = element.find('div', class_='image-container')
            if img_container:
                # Extract the image container and process it separately
                img = img_container.find('img')
                if img and img.get('src') and include_images:
                    img_path = img.get('src')
                    
                    # If it's a relative path, make it absolute
                    if not img_path.startswith('/'):
                        img_path = os.path.join(os.path.dirname(html_path), img_path)
                    
                    # Check for caption
                    caption_text = ""
                    caption = img_container.find('figcaption', class_='image-caption')
                    if caption and caption.get_text().strip():
                        caption_text = escape_latex(caption.get_text().strip())
                    
                    # Place image on its own page with max size
                    latex_content += f"""
\\clearpage
\\begin{{figure}}[p]
\\centering
\\includegraphics[width=\\textwidth,height=0.9\\textheight,keepaspectratio]{{{img_path}}}"""
                    
                    # Add caption if available
                    if caption_text:
                        latex_content += f"""
\\caption[]{{{caption_text}}}"""
                        
                    latex_content += """
\\end{figure}
\\clearpage

"""
                # Skip images entirely when images are disabled
                elif img and not include_images:
                    # Don't add anything - images and captions are skipped
                    pass
            else:
                # Check if this is the table of contents placeholder or a TOC div
                if element.name == 'div' and element.get('class'):
                    print(f"Div found with classes: {element.get('class')}")
                para_text = element.get_text().strip()
                # print(f"Element: {element.name}, Text: '{para_text[:30]}...' if too long")

                # Check for either the TABLEOFCONTENTS placeholder or if this is already a TOC div
                if para_text == "TABLEOFCONTENTS" or (element.name == 'div' and element.get('class') and 'table-of-contents' in element.get('class')):
                    print("Found TABLEOFCONTENTS placeholder, creating custom TOC...")
                    # Create a custom formatted table of contents
                    toc_content = """\\subsection*{Table of Contents}
\\vspace{0.5cm}

\\begin{longtable}{p{0.8\\textwidth}r}
"""

                    # Find all h1.title-header elements with chapter numbers
                    chapter_headings = []
                    for h1 in story_div.find_all('h1', class_='title-header'):
                        chapter_span = h1.find('span', class_='chapter-number')
                        if chapter_span:
                            chapter_num = chapter_span.get_text().strip() 
                            # Remove the chapter number to get just the title
                            heading_text = h1.get_text().replace(chapter_span.get_text(), '').strip()
                            # Get the ID for linking
                            heading_id = h1.get('id', '')
                            if heading_id:
                                chapter_headings.append((chapter_num, heading_text, heading_id))
                    
                    # Generate TOC entries
                    for chapter_num, heading_text, heading_id in chapter_headings:
                        # Format with chapter number on first line, then title, and right-justified page number with dots
                        # Replace colon with nothing (not comma)
                        chapter_num = chapter_num.replace(':', '')
                        toc_content += f"""\\noalign{{\\vspace{{2em}}}}
\\nopagebreak[4]
{{\\headingfont\\itshape {chapter_num}}} & {{}} \\\\[0.3cm]
\\nopagebreak[4]
\\multicolumn{{2}}{{p{{\\textwidth}}}}{{\\Large\\headingfont\\itshape {heading_text}}} \\\\
\\nopagebreak[4]
{{}} & {{\\headingfont\\itshape pg.~\\pageref{{{heading_id}}}}} \\\\[0.3cm]
"""
                    
                    # Close the TOC
                    toc_content += """\\end{longtable}
\\vspace{0.5cm}
"""
                    latex_content += toc_content
                else:
                    # Regular paragraph
                    para_content = process_inline_elements(element, story_div=story_div)
                    latex_content += para_content + "\n\n"
        elif element.name == 'ul':
            latex_content += process_list(element, 'itemize', story_div)
        elif element.name == 'ol':
            latex_content += process_list(element, 'enumerate', story_div)
        elif element.name == 'br':
            latex_content += "\\vspace{0.5em}\n\n"
        elif element.name == 'blockquote':
            # Process blockquotes with our fancy quote style
            quote_content = ""
            for child in element.children:
                if child.name == 'p':
                    # Process with in_quote=True to avoid redundant italic formatting
                    quote_content += process_inline_elements(child, in_quote=True, story_div=story_div) + "\n\n"
                elif child.name in ['ul', 'ol']:
                    quote_content += process_list(child, 'itemize' if child.name == 'ul' else 'enumerate', story_div)
                    
            latex_content += f"""\\begin{{fancyquote}}
{quote_content.strip()}
\\end{{fancyquote}}\\vspace{{1.2cm}}\n\n"""
        elif element.name == 'div' and 'image-container' in element.get('class', []):
            # Process image container for PDF
            img = element.find('img')
            if img and img.get('src') and include_images:
                img_path = img.get('src')
                print(f"Found image in HTML: {img_path}")
                
                # If it's a relative path, make it absolute
                if not img_path.startswith('/'):
                    abs_img_path = os.path.join(os.path.dirname(html_path), img_path)
                    print(f"Resolved to absolute path: {abs_img_path}")
                    img_path = abs_img_path
                
                # Verify the image exists
                if os.path.exists(img_path):
                    print(f"Image file exists at: {img_path}")
                else:
                    print(f"WARNING: Image file not found at: {img_path}")
                
                # Check for caption
                caption_text = ""
                caption = element.find('figcaption', class_='image-caption')
                if caption and caption.get_text().strip():
                    caption_text = escape_latex(caption.get_text().strip())
                    print(f"Found caption: {caption_text}")
                
                # Place image on its own page with max size
                latex_content += f"""
\\clearpage
\\begin{{figure}}[p]
\\centering
\\includegraphics[width=\\textwidth,height=0.9\\textheight,keepaspectratio]{{{img_path}}}"""
                
                # Add caption if available
                if caption_text:
                    latex_content += f"""
\\caption[]{{{caption_text}}}"""
                    
                latex_content += """
\\end{figure}
\\clearpage

"""
                print(f"Added image to LaTeX content with path: {img_path}")
            # Skip images entirely when images are disabled
            elif img and not include_images:
                # Don't add anything - images and captions are skipped
                pass
        elif element.name == 'div':
            # Skip description blocks that were already processed with their associated title
            if 'description-block' in element.get('class', []) and element.get('processed'):
                continue
                
            # Process other div elements as needed
            for child in element.children:
                if child.name:  # Skip text nodes
                    # Recursively process the child as if it were a direct child of story_div
                    if child.name == 'h1' or child.name == 'h2':
                        # Get the ID for label if available
                        element_id = child.get('id', '')
                        label_markup = f"\\phantomsection\\label{{{element_id}}}" if element_id else ""
                        
                        # Handle h1 elements (similar to above, but simplified)
                        header_text = process_inline_elements(child, story_div=story_div)
                        latex_content += f"{label_markup}\n\\vspace{{1.1cm}}\n\\section*{{{header_text}}}\n\\vspace{{0.3cm}}\n\n"
                    elif child.name == 'h2':
                        # Get the ID for label if available
                        element_id = child.get('id', '')
                        label_markup = f"\\phantomsection\\label{{{element_id}}}" if element_id else ""
                        
                        header_text = process_inline_elements(child, story_div=story_div)
                        latex_content += f"{label_markup}\n\\vspace{{0.1cm}}\n\\subsection*{{{header_text}}}\n\\vspace{{0.3cm}}\n\n"
                    elif child.name == 'h3':
                        # Get the ID for label if available
                        element_id = child.get('id', '')
                        label_markup = f"\\phantomsection\\label{{{element_id}}}" if element_id else ""
                        
                        header_text = process_inline_elements(child, story_div=story_div)
                        latex_content += f"{label_markup}\n\\subsubsection*{{{header_text}}}\n\\vspace{{0.2cm}}\n\n"
                    elif child.name == 'p':
                        para_content = process_inline_elements(child, story_div=story_div)
                        latex_content += para_content + "\n\n"
                    elif child.name == 'ul':
                        latex_content += process_list(child, 'itemize', story_div)
                    elif child.name == 'ol':
                        latex_content += process_list(child, 'enumerate', story_div)
    
    return LatexDocument(title=title, content=latex_content, description=description, include_images=include_images)

def process_list(list_element, list_type, story_div=None):
    """Process a list element (ul or ol) and any nested lists recursively."""
    result = f"\\begin{{{list_type}}}\n"
    
    for li in list_element.find_all('li', recursive=False):
        # Create a deep copy of the list item for processing
        li_content_element = BeautifulSoup(str(li), 'html.parser')
        
        # Find and remove nested lists from the copy for content processing
        nested_lists = []
        for nested_list in li_content_element.find_all(['ul', 'ol']):
            nested_list.extract()
        
        # Get the list item content without nested lists
        li_content = process_inline_elements(li_content_element, story_div=story_div)
        result += f"\\item {li_content}\n"
        
        # Process any nested lists from the original item
        for nested_list in li.find_all(['ul', 'ol'], recursive=False):
            if nested_list.name == 'ul':
                result += "    " + process_list(nested_list, 'itemize', story_div).replace('\n', '\n    ')
            else:  # ol
                result += "    " + process_list(nested_list, 'enumerate', story_div).replace('\n', '\n    ')
        
    result += f"\\end{{{list_type}}}\n\n"
    return result


def get_header_text_by_id(soup, element_id):
    """Find the actual header text for a given ID."""
    # Look for any element with this ID
    element = soup.find(id=element_id)
    if not element:
        return None
    
    # If it's a header, return its text
    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        return element.get_text().strip()
    
    # If it's not a header, look for the closest header in parents
    header = element.find_parent(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if header:
        return header.get_text().strip()
    
    return None

def process_inline_elements(element, in_quote=False, story_div=None) -> str:
    """Convert HTML inline elements to LaTeX syntax.
    
    Args:
        element: The BeautifulSoup element to process
        in_quote: Whether this element is within a quote environment
                 (prevents applying redundant italic formatting)
        story_div: The parent story div, used for finding header references
    """
    result = ""
    for content in element.contents:
        if content.name is None:  # Text node
            result += escape_latex(content.string or "")
        elif content.name == 'strong':
            result += f"\\textbf{{{escape_latex(content.get_text())}}}"
        elif content.name == 'em':
            # If we're already in a quote environment (which applies italics), 
            # don't add redundant italic formatting
            if in_quote:
                result += escape_latex(content.get_text())
            else:
                result += f"\\textit{{{escape_latex(content.get_text())}}}"
        elif content.name == 's':
            result += f"\\sout{{{escape_latex(content.get_text())}}}"
        elif content.name == 'u':
            result += f"\\underline{{{escape_latex(content.get_text())}}}"
        elif content.name == 'a':
            href = content.get('href', '#')
            link_text = escape_latex(content.get_text())
            
            # If this is an anchor link, create a page reference
            if href.startswith('#') and story_div:
                anchor_id = href[1:]  # Remove the # from the href
                
                # Try to find the actual header text from the referenced element
                header_text = get_header_text_by_id(story_div, anchor_id)
                
                if header_text:
                    # Use the header text instead of the link text
                    header_text = escape_latex(header_text)
                    # result += f"``{header_text}'' on page~\\pageref{{{anchor_id}}}"
                    result += f"{header_text}"
                else:
                    # Fallback to the link text if header not found
                    result += f"``{link_text}'' on page~\\pageref{{{anchor_id}}}"
            else:
                result += f"\\href{{{href}}}{{{link_text}}}"
        elif content.name == 'img':
            # Skip, images are handled separately
            pass
        else:
            # Recursively process other elements
            result += process_inline_elements(content, in_quote, story_div)
    
    return result


def escape_latex(text):
    """Escape LaTeX special characters and handle non-ASCII Unicode."""
    if text is None:
        return ""
    
    # Replace all variants of apostrophes and quotes with standard ASCII apostrophe
    text = text.replace("’", "'").replace("‘", "`").replace("”", "''").replace("“", "``")

    # Handle Unicode characters - replace with closest ASCII representation or LaTeX commands
    unicode_chars = {
        # Common punctuation
        '…': '...',
        '–': '--',
        '—': '---',
        '"': '"',
        '"': '"',
        # Apostrophes are already handled in the pre-processing step above
        '•': '\\textbullet{}',
        '≠': '$\\neq$',
        '≤': '$\\leq$',
        '≥': '$\\geq$',
        '←': '$\\leftarrow$',
        '→': '$\\rightarrow$',
        '↑': '$\\uparrow$',
        '↓': '$\\downarrow$',
        '✓': '\\checkmark{}',
        '✗': 'x',
        '✘': 'x',
        '★': '*',
        '☆': '*',
        '♦': '$\\diamond$',
        '♥': '$\\heartsuit$',
        '♠': '$\\spadesuit$',
        '♣': '$\\clubsuit$',
        '©': '\\copyright{}',
        '®': '\\textregistered{}',
        '™': '\\texttrademark{}',
        '€': '\\euro{}',
        '£': '\\pounds{}',
        '¥': '\\yen{}',
        '°': '$^{\\circ}$',
        '±': '$\\pm$',
        '×': '$\\times$',
        '÷': '$\\div$',
        '½': '$\\frac{1}{2}$',
        '¼': '$\\frac{1}{4}$',
        '¾': '$\\frac{3}{4}$',
        
        # Latin letters with diacritical marks - macrons
        'ā': '\\={a}',
        'ē': '\\={e}',
        'ī': '\\={\\i}',
        'ō': '\\={o}',
        'ū': '\\={u}',
        'Ā': '\\={A}',
        'Ē': '\\={E}',
        'Ī': '\\={I}',
        'Ō': '\\={O}',
        'Ū': '\\={U}',
        
        # Latin letters with acute accents
        'á': "\\'a",
        'é': "\\'e",
        'í': "\\'\\i",
        'ó': "\\'o",
        'ú': "\\'u",
        'Á': "\\'A",
        'É': "\\'E",
        'Í': "\\'I",
        'Ó': "\\'O",
        'Ú': "\\'U",
        
        # Latin letters with grave accents
        'à': '\\`a',
        'è': '\\`e',
        'ì': '\\`\\i',
        'ò': '\\`o',
        'ù': '\\`u',
        'À': '\\`A',
        'È': '\\`E',
        'Ì': '\\`I',
        'Ò': '\\`O',
        'Ù': '\\`U',
        
        # Latin letters with circumflex
        'â': '\\^a',
        'ê': '\\^e',
        'î': '\\^\\i',
        'ô': '\\^o',
        'û': '\\^u',
        'Â': '\\^A',
        'Ê': '\\^E',
        'Î': '\\^I',
        'Ô': '\\^O',
        'Û': '\\^U',
        
        # Latin letters with umlaut/diaeresis
        'ä': '\\"a',
        'ë': '\\"e',
        'ï': '\\"\\i',
        'ö': '\\"o',
        'ü': '\\"u',
        'Ä': '\\"A',
        'Ë': '\\"E',
        'Ï': '\\"I',
        'Ö': '\\"O',
        'Ü': '\\"U',
        
        # Other common Latin letters with diacritics
        'ç': '\\c{c}',
        'Ç': '\\c{C}',
        'ñ': '\\~n',
        'Ñ': '\\~N',
        'ÿ': '\\"y',
        'Ÿ': '\\"Y',
        'ø': '{\\o}',
        'Ø': '{\\O}',
        'å': '{\\aa}',
        'Å': '{\\AA}',
        'æ': '{\\ae}',
        'Æ': '{\\AE}',
        'œ': '{\\oe}',
        'Œ': '{\\OE}',
        'ß': '{\\ss}',
        # Emojis (we'll replace with descriptive text)
        '🤘': '[rock hand]',
        '👉': '[pointing right]',
        '👈': '[pointing left]',
        '👆': '[pointing up]',
        '👇': '[pointing down]',
        '👍': '[thumbs up]',
        '👎': '[thumbs down]',
        '😊': '[smile]',
        '😀': '[smile]',
        '😃': '[smile]',
        '😄': '[smile]',
        '😁': '[smile]',
        '😆': '[smile]',
        '😅': '[smile]',
        '😂': '[laugh]',
        '🤣': '[laugh]',
        '😉': '[wink]',
        '😎': '[cool]',
        '🙂': '[smile]',
        '🙃': '[upside-down face]',
        '🙄': '[eye roll]',
        '😐': '[neutral face]',
        '😑': '[neutral face]',
        '😶': '[no mouth]',
        '😣': '[persevere]',
        '😥': '[sad]',
        '😮': '[surprised]',
        '😯': '[surprised]',
        '😪': '[sleepy]',
        '😫': '[tired]',
        '😴': '[sleeping]',
        '😌': '[relieved]',
        '😛': '[tongue out]',
        '😜': '[wink tongue]',
        '😝': '[tongue closed eyes]',
        '🙁': '[frown]',
        '😒': '[unamused]',
        '😓': '[downcast]',
        '😔': '[pensive]',
        '😕': '[confused]',
        '😖': '[confounded]',
        '😞': '[disappointed]',
        '😟': '[worried]',
        '😢': '[crying]',
        '😭': '[sobbing]',
        '😤': '[triumphant]',
        '😠': '[angry]',
        '😡': '[pouting]',
        '😳': '[flushed]',
        '😱': '[scared]',
        '😨': '[fearful]',
        '😰': '[anxious]',
        '😷': '[mask]',
    }
    
    # Escape LaTeX special characters
    chars = {
        '&': '\\&',
        '%': '\\%',
        '$': '\\$',
        '#': '\\#',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
        '^': '\\textasciicircum{}',
        '\\': '\\textbackslash{}',
    }
    
    # First replace backslash, then other characters
    text = text.replace('\\', '\\textbackslash{}')

    # Now replace other special characters
    for char, replacement in chars.items():
        if char != '\\':  # Already handled backslash
            text = text.replace(char, replacement)

    # Replace Unicode characters with their LaTeX equivalents
    for char, replacement in unicode_chars.items():
        text = text.replace(char, replacement)

    # Process remaining non-ASCII characters with LaTeX encoding
    result = []
    for c in text:
        if ord(c) < 128:
            result.append(c)  # ASCII characters unchanged
        else:
            # For other Unicode characters, use LaTeX decimal representation
            result.append(f"\\symbol{{{ord(c)}}}")
    
    text = ''.join(result)

    return text


def check_pdflatex_installed():
    """Check if pdflatex is installed."""
    try:
        result = subprocess.run(['which', 'pdflatex'], 
                             check=False, capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def latex_to_pdf(latex_content, output_path):
    """Convert LaTeX content to PDF using pdflatex."""
    # Check if pdflatex is installed
    if not check_pdflatex_installed():
        print("Error: pdflatex is not installed. Please install it using:")
        print("  sudo apt-get install texlive-latex-base texlive-fonts-recommended texlive-latex-extra")
        print(f"\nTeX file has been saved to {os.path.basename(output_path).replace('.pdf', '.tex')}")
        return
        
    # Get the base filename from the output path
    base_filename = os.path.basename(output_path).replace('.pdf', '')
    temp_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else '.'
    tex_path = os.path.join(temp_dir, f'{base_filename}.tex')
    
    with open(tex_path, 'w') as f:
        f.write(latex_content)
    
    # Run pdflatex twice to resolve references
    try:
        # Change to the directory containing the tex file for pdflatex
        current_dir = os.getcwd()
        os.chdir(temp_dir)
        
        # First check if xelatex (better Unicode support) is installed
        try:
            xelatex_result = subprocess.run(['which', 'xelatex'], 
                                         check=False, capture_output=True, text=True)
            has_xelatex = xelatex_result.returncode == 0
        except Exception:
            has_xelatex = False
            
        # Use xelatex if available, otherwise fallback to pdflatex
        tex_filename = os.path.basename(tex_path)
        latex_engine = 'xelatex' if has_xelatex else 'pdflatex'
        
        print(f"Using {latex_engine} for PDF generation...")
        
        subprocess.run([latex_engine, '-interaction=nonstopmode', tex_filename], 
                       check=True, capture_output=True)
        subprocess.run([latex_engine, '-interaction=nonstopmode', tex_filename], 
                       check=True, capture_output=True)
        
        # Move back to original directory
        os.chdir(current_dir)
        
        # Move the PDF to the desired output path if it's not already there
        pdf_path = tex_path.replace('.tex', '.pdf')
        if pdf_path != output_path and os.path.exists(pdf_path):
            os.rename(pdf_path, output_path)
            
        print(f"PDF successfully created at {output_path}")
        
        # Clean up auxiliary files
        for ext in ['.aux', '.log', '.out', '.toc', '.lof', '.lot']:
            aux_file = tex_path.replace('.tex', ext)
            if os.path.exists(aux_file):
                os.remove(aux_file)
                
        # We now keep the .tex file with the same name as the pdf
        
    except subprocess.CalledProcessError as e:
        print(f"Error running pdflatex: {e}")
        if hasattr(e, 'stdout') and e.stdout:
            print(f"STDOUT: {e.stdout.decode()}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"STDERR: {e.stderr.decode()}")
        print(f"\nTeX file has been saved to {tex_path}")
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        print(f"\nTeX file has been saved to {tex_path}")


def ensure_latex_templates_dir():
    """Ensure the LaTeX templates directory exists."""
    templates_dir = os.path.join(os.path.dirname(__file__), "latex_templates")
    if not os.path.exists(templates_dir):
        try:
            os.makedirs(templates_dir)
            print(f"Created templates directory: {templates_dir}")
        except Exception as e:
            print(f"Warning: Could not create templates directory: {e}")
    return templates_dir

def modify_html_for_latex(html_path, modified_html_path):
    """Modify HTML for LaTeX conversion and save to a new file."""
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # # Find the first h1 with class title-header
    # first_title = soup.find('h1', class_='title-header')
    # if first_title:
    #     # Empty the text content but keep the element
    #     first_title.string = ""
    #     print(f"First h1 title-header emptied successfully in {modified_html_path}.")
    # else:
    #     print(f"No h1 title-header found in the HTML file {html_path}.")
    
    # Write the modified HTML to the new file
    with open(modified_html_path, 'w') as f:
        f.write(str(soup))
    
    return modified_html_path

def main():
    parser = argparse.ArgumentParser(description='Convert governance HTML to PDF')
    parser.add_argument('--output', default='liberty_by_design.pdf',
                        help='Output PDF file path')
    parser.add_argument('--include-images', action='store_true',
                        help='Include images in the PDF (default: false)')
    parser.add_argument('--skip-site-generation', action='store_true',
                        help='Skip generating the site before creating PDF')
    parser.add_argument('--pdf-only', action='store_true',
                        help='Only regenerate PDF from existing LaTeX file, skip site and LaTeX generation')
    parser.add_argument('--local-only', action='store_true',
                        help='Use cached documents only without connecting to Google')
    parser.add_argument('--mobile-only', action='store_true',
                        help='Generate only the mobile version')
    parser.add_argument('--print-only', action='store_true',
                        help='Generate only the print version')
    args = parser.parse_args()
    
    # Determine which versions to generate
    generate_print = not args.mobile_only
    generate_mobile = not args.print_only
    
    # Get the output base name without extension for creating both formats
    output_base = os.path.splitext(args.output)[0]
    
    # If pdf-only flag is set, skip site and LaTeX generation
    if args.pdf_only:
        if generate_print:
            print_tex_filename = f"{output_base}.tex"
            if not os.path.exists(print_tex_filename):
                print(f"Error: LaTeX file {print_tex_filename} not found. Run without --pdf-only flag first.")
                sys.exit(1)
            
            # Read existing LaTeX file
            with open(print_tex_filename, 'r') as f:
                print_latex_content = f.read()
                
            # Convert LaTeX to PDF
            print(f"Regenerating print PDF from existing LaTeX file {print_tex_filename}...")
            latex_to_pdf(print_latex_content, f"{output_base}.pdf")
            
        if generate_mobile:
            mobile_tex_filename = f"{output_base}_mobile.tex"
            if not os.path.exists(mobile_tex_filename):
                print(f"Error: LaTeX file {mobile_tex_filename} not found. Run without --pdf-only flag first.")
                sys.exit(1)
            
            # Read existing LaTeX file
            with open(mobile_tex_filename, 'r') as f:
                mobile_latex_content = f.read()
                
            # Convert LaTeX to PDF
            print(f"Regenerating mobile PDF from existing LaTeX file {mobile_tex_filename}...")
            latex_to_pdf(mobile_latex_content, f"{output_base}_mobile.pdf")
    else:
        # Generate site using make_governance.py instead of generate_site.py
        if not args.skip_site_generation:
            print("Running make_governance.py first...")
            make_governance.main(local_only=args.local_only)
            print("Site generation completed successfully.")
        
        # Ensure LaTeX templates directory exists
        ensure_latex_templates_dir()
        
        # Process each version from liberty_by_design_versions.py
        for version in liberty_versions:
            version_uri = version.uri
            
            # Skip if not needed based on flags
            if (version.physical_version and not generate_print) or (not version.physical_version and not generate_mobile):
                continue
                
            html_path = os.path.join('posts', f"{version_uri}.html")
            
            if not os.path.exists(html_path):
                print(f"Error: HTML file {html_path} not found. Make sure make_governance.py has been run.")
                continue
            
            # Create a modified HTML file for LaTeX conversion
            modified_html_path = html_path + ".modified.html"
            modify_html_for_latex(html_path, modified_html_path)
            
            # Convert HTML to LaTeX
            print(f"Converting {modified_html_path} to LaTeX...")
            latex_content_base = html_to_latex(modified_html_path, include_images=args.include_images)
            
            # Determine template type based on version
            template_type = "print" if version.physical_version else "mobile"
            print(f"Using template type: {template_type} for version {version_uri}")
            
            # Generate LaTeX document
            latex_doc = LatexDocument(
                title=latex_content_base.title,
                content=latex_content_base.content,
                description=latex_content_base.description,
                include_images=latex_content_base.include_images,
                template_type=template_type
            )
            
            # Generate the LaTeX content
            latex_content = latex_doc.to_latex()
            
            # Write LaTeX to file
            tex_filename = f"{version_uri}.tex"
            with open(tex_filename, 'w') as f:
                f.write(latex_content)
            
            # Convert LaTeX to PDF
            print(f"Converting LaTeX to PDF for {version_uri}...")
            pdf_filename = f"{version_uri}.pdf"
            latex_to_pdf(latex_content, pdf_filename)


if __name__ == "__main__":
    main()