#!/usr/bin/env python3
import os
import sys
import re
import argparse
from bs4 import BeautifulSoup
import subprocess
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class LatexDocument:
    title: str
    content: str
    description: Optional[str] = None
    
    def to_latex(self) -> str:
        """Generate a complete LaTeX document string using template file."""
        template_path = os.path.join(os.path.dirname(__file__), "latex_templates", "a5_booklet_template.tex")
        
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

% A5 papersize
\\usepackage[a5paper, inner=20mm, outer=10mm, top=15mm, bottom=15mm, twoside]{geometry}

% Styling
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
\\vspace*{1cm}
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


def html_to_latex(html_path: str) -> LatexDocument:
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
        title = "Tiny Book on Governance of Machine Intelligence"
    else:
        title = title_element.get_text().strip()
    
    # Escape LaTeX special characters in title
    title = escape_latex(title)
    
    # Get description if available
    description = None
    description_block = story_div.find('div', class_='description-block')
    if description_block:
        description = ' '.join([p.get_text().strip() for p in description_block.find_all('p')])
        description = escape_latex(description)
    
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
            # Only add page break if it's a title header (new document being inlined)
            if 'title-header' in element.get('class', []):
                # Add spacing after page break before the title header
                latex_content += f"\\clearpage\n\\vspace*{{1.5cm}}\n\\section*{{{escape_latex(element.get_text().strip())}}}\n\\vspace{{0.7cm}}\n\n"
                
                # Look for a description block right after this title
                next_elem = element.find_next_sibling()
                if next_elem and next_elem.name == 'div' and 'description-block' in next_elem.get('class', []):
                    desc_text = ' '.join([p.get_text().strip() for p in next_elem.find_all('p')])
                    desc_text = escape_latex(desc_text)
                    latex_content += f"""\\begin{{fancyquote}}
{desc_text}
\\end{{fancyquote}}\n\n"""
                    # Skip this description block when we encounter it in the normal loop
                    next_elem['processed'] = True
            else:
                latex_content += f"\\section*{{{escape_latex(element.get_text().strip())}}}\n\\vspace{{0.5cm}}\n\n"
        elif element.name == 'h2':
            latex_content += f"\\needspace{{3\\baselineskip}}\n\\subsection*{{{escape_latex(element.get_text().strip())}}}\n\\vspace{{0.3cm}}\n\n"
        elif element.name == 'h3':
            latex_content += f"\\needspace{{2\\baselineskip}}\n\\subsubsection*{{{escape_latex(element.get_text().strip())}}}\n\\vspace{{0.2cm}}\n\n"
        elif element.name == 'p':
            # Check if this is a quote block (typically italicized paragraphs)
            is_quote = element.find('em') and len(element.contents) == 1 and element.contents[0].name == 'em'
            
            if is_quote:
                # If the entire paragraph is in italics, treat it as a quote
                # Process with in_quote=True to avoid redundant italic formatting
                para_content = process_inline_elements(element, in_quote=True)
                latex_content += f"""\\begin{{fancyquote}}
{para_content}
\\end{{fancyquote}}\n\n"""
            else:
                # Regular paragraph
                para_content = process_inline_elements(element)
                latex_content += para_content + "\n\n"
        elif element.name == 'ul':
            latex_content += process_list(element, 'itemize')
        elif element.name == 'ol':
            latex_content += process_list(element, 'enumerate')
        elif element.name == 'br':
            latex_content += "\\vspace{0.5em}\n\n"
        elif element.name == 'blockquote':
            # Process blockquotes with our fancy quote style
            quote_content = ""
            for child in element.children:
                if child.name == 'p':
                    # Process with in_quote=True to avoid redundant italic formatting
                    quote_content += process_inline_elements(child, in_quote=True) + "\n\n"
                elif child.name in ['ul', 'ol']:
                    quote_content += process_list(child, 'itemize' if child.name == 'ul' else 'enumerate')
                    
            latex_content += f"""\\begin{{fancyquote}}
{quote_content.strip()}
\\end{{fancyquote}}\n\n"""
        elif element.name == 'div':
            # Skip description blocks that were already processed with their associated title
            if 'description-block' in element.get('class', []) and element.get('processed'):
                continue
                
            # Process other div elements as needed
            for child in element.children:
                if child.name:  # Skip text nodes
                    # Recursively process the child as if it were a direct child of story_div
                    if child.name == 'h1':
                        # Handle h1 elements (similar to above, but simplified)
                        latex_content += f"\\section*{{{escape_latex(child.get_text().strip())}}}\n\\vspace{{0.5cm}}\n\n"
                    elif child.name == 'h2':
                        latex_content += f"\\subsection*{{{escape_latex(child.get_text().strip())}}}\n\\vspace{{0.3cm}}\n\n"
                    elif child.name == 'h3':
                        latex_content += f"\\subsubsection*{{{escape_latex(child.get_text().strip())}}}\n\\vspace{{0.2cm}}\n\n"
                    elif child.name == 'p':
                        para_content = process_inline_elements(child)
                        latex_content += para_content + "\n\n"
                    elif child.name == 'ul':
                        latex_content += process_list(child, 'itemize')
                    elif child.name == 'ol':
                        latex_content += process_list(child, 'enumerate')
    
    return LatexDocument(title=title, content=latex_content, description=description)

def process_list(list_element, list_type):
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
        li_content = process_inline_elements(li_content_element)
        result += f"\\item {li_content}\n"
        
        # Process any nested lists from the original item
        for nested_list in li.find_all(['ul', 'ol'], recursive=False):
            if nested_list.name == 'ul':
                result += "    " + process_list(nested_list, 'itemize').replace('\n', '\n    ')
            else:  # ol
                result += "    " + process_list(nested_list, 'enumerate').replace('\n', '\n    ')
        
    result += f"\\end{{{list_type}}}\n\n"
    return result


def process_inline_elements(element, in_quote=False) -> str:
    """Convert HTML inline elements to LaTeX syntax.
    
    Args:
        element: The BeautifulSoup element to process
        in_quote: Whether this element is within a quote environment
                 (prevents applying redundant italic formatting)
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
            result += f"\\st{{{escape_latex(content.get_text())}}}"
        elif content.name == 'u':
            result += f"\\underline{{{escape_latex(content.get_text())}}}"
        elif content.name == 'a':
            href = content.get('href', '#')
            text = escape_latex(content.get_text())
            result += f"\\href{{{href}}}{{{text}}}"
        else:
            # Recursively process other elements
            result += process_inline_elements(content, in_quote)
    
    return result


def escape_latex(text):
    """Escape LaTeX special characters and handle non-ASCII Unicode."""
    if text is None:
        return ""
    
    # Replace all variants of apostrophes with standard ASCII apostrophe
    text = text.replace("'", "'")  # right single quotation mark
    text = text.replace("'", "'")  # left single quotation mark
    
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
    
    # Replace Unicode characters with their LaTeX equivalents
    for char, replacement in unicode_chars.items():
        text = text.replace(char, replacement)
    
    # Remove any remaining non-ASCII characters
    text = ''.join(c if ord(c) < 128 else ' ' for c in text)
    
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

def main():
    parser = argparse.ArgumentParser(description='Convert governance HTML to PDF')
    parser.add_argument('--output', default='tiny_book_on_governance_of_machine.pdf',
                        help='Output PDF file path')
    args = parser.parse_args()
    
    # Ensure LaTeX templates directory exists
    ensure_latex_templates_dir()
    
    # Path to the governance HTML file
    html_path = os.path.join('posts', 'tiny_book_on_governance_of_machine.html')
    
    if not os.path.exists(html_path):
        print(f"Error: HTML file {html_path} not found. Make sure the site has been generated.")
        sys.exit(1)
    
    # Convert HTML to LaTeX
    print(f"Converting {html_path} to LaTeX...")
    latex_doc = html_to_latex(html_path)
    
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


if __name__ == "__main__":
    main()