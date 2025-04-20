#!/usr/bin/env python3
import os
import sys
import re
import argparse
from bs4 import BeautifulSoup
import subprocess
from dataclasses import dataclass
from typing import List, Optional
import generate_site

@dataclass
class LatexDocument:
    title: str
    content: str
    description: Optional[str] = None
    include_images: bool = False
    
    def to_latex(self) -> str:
        """Generate a complete LaTeX document string using template file."""
        template_path = os.path.join(os.path.dirname(__file__), "latex_templates", "pocket_book_template.tex")
        
        try:
            with open(template_path, "r") as f:
                template = f.read()
        except FileNotFoundError:
            # Fallback if template file is missing
            print(f"Warning: Template file {template_path} not found. Using built-in template.")
            return self._generate_fallback_template()
            
        # Prepare description block with page break after
        description_block = ""
        if self.description:
            description_block = f"""
\\begin{{fancyquote}}
{self.description}
\\end{{fancyquote}}

\\clearpage
"""

        # Replace placeholders in template
        latex = template.replace("$title$", self.title)
        latex = latex.replace("$main_description$", self.description or "")
        latex = latex.replace("$content$", self.content)
        
        return latex
        
    def _generate_fallback_template(self) -> str:
        """Generate a fallback LaTeX document if template file is missing."""
        latex = """\\documentclass[12pt,twoside]{book}

% LaTeX engine detection
\\usepackage{ifxetex}
\\ifxetex
  % XeTeX-specific settings for better Unicode support
  \\usepackage{fontspec}
  \\setmainfont{Times New Roman}
  \\usepackage{xunicode}
  \\usepackage{xltxtra}
\\else
  % pdfTeX settings
  \\usepackage[utf8]{inputenc}
  \\usepackage[T1]{fontenc}
  \\usepackage{lmodern}
  \\usepackage{textcomp}  % Extended text companion symbols
  \\usepackage{upquote}   % Straight quotes in verbatim environments
\\fi

\\usepackage{microtype}
\\usepackage{graphicx}
\\usepackage{hyperref}
\\usepackage{setspace}
\\usepackage{parskip}
\\usepackage{color}
\\usepackage{soul}
\\usepackage{titlesec}
\\usepackage{mdframed}
\\usepackage{xcolor}
\\usepackage{needspace}
\\usepackage{afterpage}
\\usepackage{caption}

% Configure hyperref for better internal references
\\hypersetup{
  colorlinks=false,  % No colored links for print
  pdfborder={0 0 0}, % Remove link borders
  pdftitle={""" + self.title + """},
  bookmarks=true,
  pdfpagemode=FullScreen,
}

% A5 papersize
\\usepackage[a5paper, inner=20mm, outer=10mm, top=15mm, bottom=15mm, twoside]{geometry}

% Styling
\\captionsetup{labelformat=empty}
\\setstretch{1.15}
\\setlength{\\parindent}{0pt}

% Custom quote environment
\\definecolor{quotecolor}{rgb}{0.4,0.4,0.4}
\\definecolor{quotebackground}{rgb}{0.97,0.97,0.97}
\\definecolor{quoteborder}{rgb}{0.85,0.85,0.85}

\\newenvironment{fancyquote}{%
  \\begin{mdframed}[
    linecolor=quoteborder,
    backgroundcolor=quotebackground,
    linewidth=1pt,
    leftmargin=0pt,
    rightmargin=0pt,
    innerleftmargin=10pt,
    innerrightmargin=10pt,
    innertopmargin=10pt,
    innerbottommargin=10pt,
    roundcorner=5pt
  ]
  \\color{quotecolor}
  \\itshape
}{%
  \\end{mdframed}
}

\\title{""" + self.title + """}
\\author{Jordan Ezra Fisher}
\\date{\\today}

\\begin{document}

\\frontmatter
\\maketitle
\\thispagestyle{empty}
"""
        
        # Add description as a styled quote with extra spacing if available
        if self.description:
            latex += """
\\begin{center}
\\vspace*{7cm}
\\begin{fancyquote}
""" + self.description + """
\\end{fancyquote}
\\vspace*{0.5cm}
\\end{center}
"""

        latex += """
\\mainmatter
\\setcounter{page}{1}

\\clearpage
\\begin{center}
\\vspace*{1cm}
{\\Large\\bfseries """ + self.title + """}
\\vspace*{1cm}
\\end{center}

""" + self.content + """

\\end{document}
"""
        
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
    title_element = story_div.find('h1', class_='title-header')
    if not title_element:
        title_element = story_div.find('h1')
    
    if not title_element:
        # title = "Tiny Book on Governance of Machine Intelligence"
        title = "Liberty by Design"
    else:
        # Process the title element to preserve formatting
        title = process_inline_elements(title_element)
    
    # No need to escape LaTeX special characters as process_inline_elements already did that
    
    # Get description if available
    description = None
    description_block = story_div.find('div', class_='description-block')
    if description_block:
        # Process each paragraph with formatting and join them
        description = ' '.join([process_inline_elements(p, story_div=story_div) for p in description_block.find_all('p')])
    
    # Process all elements in the HTML body
    latex_content = ""
    
    # Remove the title and description before processing content
    if title_element:
        title_element.extract()
    if description_block:
        description_block.extract()
    
    for element in story_div.children:
        if element.name is None:  # Skip text nodes
            continue
            
        if element.name == 'h1':
            # Get the ID for label if available
            element_id = element.get('id', '')
            label_markup = f"\\label{{{element_id}}}" if element_id else ""
            
            # Only add page break if it's a title header (new document being inlined)
            if 'title-header' in element.get('class', []):
                # Add spacing after page break before the title header
                # Process the header with formatting (bold, italic, strikethrough)
                
                # Check for chapter number
                chapter_number_tag = element.find('span', class_='chapter-number')
                chapter_prefix = ""
                
                if chapter_number_tag:
                    chapter_prefix = f"\\textit{{{chapter_number_tag.get_text().strip()}}} "
                    # Remove the chapter number span from the element for regular processing
                    chapter_number_tag.extract()
                
                header_text = process_inline_elements(element, story_div=story_div)
                latex_content += f"\\clearpage\n\\vspace*{{1.5cm}}\n\\section*{{{chapter_prefix}{header_text}}}{label_markup}\n\\vspace{{0.7cm}}\n\n"
                
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
                    chapter_prefix = f"\\textit{{{chapter_number_tag.get_text().strip()}}} "
                    # Remove the chapter number span from the element for regular processing
                    chapter_number_tag.extract()
                
                header_text = process_inline_elements(element, story_div=story_div)
                latex_content += f"\\section*{{{chapter_prefix}{header_text}}}{label_markup}\n\\vspace{{0.5cm}}\n\n"
        elif element.name == 'h2':
            # Get the ID for label if available
            element_id = element.get('id', '')
            label_markup = f"\\label{{{element_id}}}" if element_id else ""
            
            header_text = process_inline_elements(element, story_div=story_div)
            latex_content += f"\\needspace{{3\\baselineskip}}\n\\subsection*{{{header_text}}}{label_markup}\n\\vspace{{0.3cm}}\n\n"
        elif element.name == 'h3':
            # Get the ID for label if available
            element_id = element.get('id', '')
            label_markup = f"\\label{{{element_id}}}" if element_id else ""
            
            header_text = process_inline_elements(element, story_div=story_div)
            latex_content += f"\\needspace{{2\\baselineskip}}\n\\subsubsection*{{{header_text}}}{label_markup}\n\\vspace{{0.2cm}}\n\n"
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
# Skipping this for now. We don't want <em> blocks to become fancyquotes.
#             # Check if this is a quote block (typically italicized paragraphs)
#             elif element.find('em') and len(element.contents) == 1 and element.contents[0].name == 'em':
#                 # If the entire paragraph is in italics, treat it as a quote
#                 # Process with in_quote=True to avoid redundant italic formatting
#                 para_content = process_inline_elements(element, in_quote=True, story_div=story_div)
#                 latex_content += f"""\\begin{{fancyquote}}
# {para_content}
# \\end{{fancyquote}}\\vspace{{1.2cm}}\n\n"""
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
                    if child.name == 'h1':
                        # Get the ID for label if available
                        element_id = child.get('id', '')
                        label_markup = f"\\label{{{element_id}}}" if element_id else ""
                        
                        # Handle h1 elements (similar to above, but simplified)
                        header_text = process_inline_elements(child, story_div=story_div)
                        latex_content += f"\\section*{{{header_text}}}{label_markup}\n\\vspace{{0.5cm}}\n\n"
                    elif child.name == 'h2':
                        # Get the ID for label if available
                        element_id = child.get('id', '')
                        label_markup = f"\\label{{{element_id}}}" if element_id else ""
                        
                        header_text = process_inline_elements(child, story_div=story_div)
                        latex_content += f"\\subsection*{{{header_text}}}{label_markup}\n\\vspace{{0.3cm}}\n\n"
                    elif child.name == 'h3':
                        # Get the ID for label if available
                        element_id = child.get('id', '')
                        label_markup = f"\\label{{{element_id}}}" if element_id else ""
                        
                        header_text = process_inline_elements(child, story_div=story_div)
                        latex_content += f"\\subsubsection*{{{header_text}}}{label_markup}\n\\vspace{{0.2cm}}\n\n"
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
                    result += f"``{header_text}'' on page~\\pageref{{{anchor_id}}}"
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

    # Handle Unicode characters - replace with closest ASCII representation or remove
    # This is a simple approach; for a more comprehensive solution, consider a Unicode to LaTeX package
    unicode_chars = {
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

    # Remove any remaining non-ASCII characters
    text = ''.join(c if ord(c) < 128 else ' ' for c in text)

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

def merge_pdf_with_cover(original_pdf, cover_pdf, output_pdf):
    """Merge a PDF with a custom cover and back page."""
    try:
        # Check if PyPDF2 is installed
        import PyPDF2
    except ImportError:
        print("Error: PyPDF2 is not installed. Please install it using 'pip install PyPDF2'.")
        return False
    
    try:
        # Open the original PDF and the cover PDF
        with open(original_pdf, 'rb') as pdf_file, open(cover_pdf, 'rb') as cover_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            cover_reader = PyPDF2.PdfReader(cover_file)
            
            # Create a new PDF writer
            pdf_writer = PyPDF2.PdfWriter()
            
            # Add the cover page (first page of cover_pdf)
            if len(cover_reader.pages) > 0:
                pdf_writer.add_page(cover_reader.pages[0])
            
            # # Add all pages from the original PDF (except the first page)
            # for page_num in range(1, len(pdf_reader.pages)):
            #     pdf_writer.add_page(pdf_reader.pages[page_num])

            # Add all pages from the original PDF (including the first page)
            for page_num in range(len(pdf_reader.pages)):
                pdf_writer.add_page(pdf_reader.pages[page_num])

            # Add the back page (second page of cover_pdf)
            if len(cover_reader.pages) > 1:
                pdf_writer.add_page(cover_reader.pages[1])
            
            # Write the result to the output file
            with open(output_pdf, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            print(f"Successfully created PDF with custom cover at {output_pdf}")
            return True
            
    except Exception as e:
        print(f"Error merging PDFs: {e}")
        return False
        
def main():
    parser = argparse.ArgumentParser(description='Convert governance HTML to PDF')
    parser.add_argument('--output', default='tiny_book_on_governance_of_machine.pdf',
                        help='Output PDF file path')
    parser.add_argument('--include-images', action='store_true',
                        help='Include images in the PDF (default: false)')
    parser.add_argument('--skip-site-generation', action='store_true',
                        help='Skip generating the site before creating PDF')
    args = parser.parse_args()
    
    # Generate site first to ensure HTML files are up-to-date
    if not args.skip_site_generation:
        print("Generating site first...")
        try:
            generate_site.main()
            print("Site generation completed successfully.")
        except Exception as e:
            print(f"Error generating site: {e}")
            sys.exit(1)
    
    # Ensure LaTeX templates directory exists
    ensure_latex_templates_dir()
    
    # Path to the governance HTML file
    html_path = os.path.join('posts', 'tiny_book_on_governance_of_machine.html')
    
    if not os.path.exists(html_path):
        print(f"Error: HTML file {html_path} not found. Make sure the site has been generated.")
        sys.exit(1)
    
    # Convert HTML to LaTeX
    print(f"Converting {html_path} to LaTeX...")
    latex_doc = html_to_latex(html_path, include_images=args.include_images)
    
    # Generate the LaTeX content
    latex_content = latex_doc.to_latex()
    
    # Get the TeX filename from the output PDF filename
    tex_filename = os.path.basename(args.output).replace('.pdf', '.tex')
    
    # Write LaTeX to file with the same base name as the PDF
    with open(tex_filename, 'w') as f:
        f.write(latex_content)
    
    # Convert LaTeX to PDF
    print(f"Converting LaTeX to PDF...")
    latex_to_pdf(latex_content, args.output)
    
    # Always create a second version with custom cover
    # Path to the cover PDF
    # cover_pdf = os.path.join('tiny_book_on_governance', 'cover_design_singularity_1.pdf')
    cover_pdf = os.path.join('tiny_book_on_governance', 'cover_design_liberty_2.pdf')    

    if not os.path.exists(cover_pdf):
        print(f"Error: Cover PDF {cover_pdf} not found.")
        return
    
    # Generate output filename for the version with cover
    output_with_cover = args.output.replace('.pdf', '_with_cover.pdf')
    
    # Merge the PDFs
    print(f"Creating version with custom cover...")
    merge_pdf_with_cover(args.output, cover_pdf, output_with_cover)


if __name__ == "__main__":
    main()