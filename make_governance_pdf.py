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
        """Generate a complete LaTeX document string."""
        latex = (
            "\\documentclass[12pt]{article}\n"
            "\\usepackage[utf8]{inputenc}\n"
            "\\usepackage[T1]{fontenc}\n"
            "\\usepackage{lmodern}\n"
            "\\usepackage{microtype}\n"
            "\\usepackage{graphicx}\n"
            "\\usepackage{hyperref}\n"
            "\\usepackage{geometry}\n"
            "\\usepackage{setspace}\n"
            "\\usepackage{parskip}\n"
            "\\usepackage{color}\n"
            "\\usepackage{soul}\n"
            "\n"
            "\\geometry{a4paper, margin=1.2in}\n"
            "\\setstretch{1.15}\n"
            "\\setlength{\\parindent}{0pt}\n"
            "\n"
            f"\\title{{{self.title}}}\n"
            "\\author{Jordan Ezra Fisher}\n"
            "\\date{\\today}\n"
            "\n"
            "\\begin{document}\n"
            "\n"
            "\\maketitle\n"
            "\n"
        )
        
        # Add description as a quote if available
        if self.description:
            latex += (
                "\\begin{quote}\n"
                "\\textit{" + self.description + "}\n"
                "\\end{quote}\n\n"
            )
        
        # Add content
        latex += self.content + "\n"
        
        # End document
        latex += "\\end{document}\n"
        
        return latex


def html_to_latex(html_path: str) -> LatexDocument:
    """Convert HTML file to LaTeX document."""
    
    with open(html_path, 'r') as f:
        html_content = f.read()
    
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
            latex_content += f"\\section*{{{escape_latex(element.get_text().strip())}}}\n\n"
        elif element.name == 'h2':
            latex_content += f"\\subsection*{{{escape_latex(element.get_text().strip())}}}\n\n"
        elif element.name == 'h3':
            latex_content += f"\\subsubsection*{{{escape_latex(element.get_text().strip())}}}\n\n"
        elif element.name == 'p':
            # Process paragraph with inline formatting
            para_content = process_inline_elements(element)
            latex_content += para_content + "\n\n"
        elif element.name == 'ul':
            latex_content += "\\begin{itemize}\n"
            for li in element.find_all('li', recursive=False):
                li_content = process_inline_elements(li)
                # Handle nested lists
                nested_list = li.find(['ul', 'ol'])
                if nested_list:
                    # Remove the nested list from the li content
                    nested_list.extract()
                    li_content = process_inline_elements(li)
                    latex_content += f"\\item {li_content}\n"
                    if nested_list.name == 'ul':
                        latex_content += "\\begin{itemize}\n"
                        for nested_li in nested_list.find_all('li'):
                            nested_content = process_inline_elements(nested_li)
                            latex_content += f"\\item {nested_content}\n"
                        latex_content += "\\end{itemize}\n"
                    elif nested_list.name == 'ol':
                        latex_content += "\\begin{enumerate}\n"
                        for nested_li in nested_list.find_all('li'):
                            nested_content = process_inline_elements(nested_li)
                            latex_content += f"\\item {nested_content}\n"
                        latex_content += "\\end{enumerate}\n"
                else:
                    latex_content += f"\\item {li_content}\n"
            latex_content += "\\end{itemize}\n\n"
        elif element.name == 'ol':
            latex_content += "\\begin{enumerate}\n"
            for li in element.find_all('li', recursive=False):
                li_content = process_inline_elements(li)
                latex_content += f"\\item {li_content}\n"
            latex_content += "\\end{enumerate}\n\n"
        elif element.name == 'br':
            latex_content += "\\vspace{0.5em}\n\n"
    
    return LatexDocument(title=title, content=latex_content, description=description)


def process_inline_elements(element) -> str:
    """Convert HTML inline elements to LaTeX syntax."""
    result = ""
    for content in element.contents:
        if content.name is None:  # Text node
            result += escape_latex(content.string or "")
        elif content.name == 'strong':
            result += f"\\textbf{{{escape_latex(content.get_text())}}}"
        elif content.name == 'em':
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
            result += process_inline_elements(content)
    
    return result


def escape_latex(text):
    """Escape LaTeX special characters."""
    if text is None:
        return ""
        
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
        print("\nTeX file has been saved to governance.tex")
        return
        
    # Write LaTeX content to a temporary file
    temp_dir = os.path.dirname(output_path) if os.path.dirname(output_path) else '.'
    tex_path = os.path.join(temp_dir, 'governance.tex')
    
    with open(tex_path, 'w') as f:
        f.write(latex_content)
    
    # Run pdflatex twice to resolve references
    try:
        # Change to the directory containing the tex file for pdflatex
        current_dir = os.getcwd()
        os.chdir(temp_dir)
        
        # Run pdflatex
        subprocess.run(['pdflatex', '-interaction=nonstopmode', 'governance.tex'], 
                       check=True, capture_output=True)
        subprocess.run(['pdflatex', '-interaction=nonstopmode', 'governance.tex'], 
                       check=True, capture_output=True)
        
        # Move back to original directory
        os.chdir(current_dir)
        
        # Move the PDF to the desired output path if it's not already there
        pdf_path = os.path.join(temp_dir, 'governance.pdf')
        if pdf_path != output_path and os.path.exists(pdf_path):
            os.rename(pdf_path, output_path)
            
        print(f"PDF successfully created at {output_path}")
        
        # Clean up auxiliary files
        for ext in ['.aux', '.log', '.out', '.toc', '.lof', '.lot']:
            aux_file = os.path.join(temp_dir, f'governance{ext}')
            if os.path.exists(aux_file):
                os.remove(aux_file)
                
        # Optionally keep or remove the .tex file
        # os.remove(tex_path)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running pdflatex: {e}")
        if hasattr(e, 'stdout') and e.stdout:
            print(f"STDOUT: {e.stdout.decode()}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"STDERR: {e.stderr.decode()}")
        print("\nTeX file has been saved to governance.tex")
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        print("\nTeX file has been saved to governance.tex")


def main():
    parser = argparse.ArgumentParser(description='Convert governance HTML to PDF')
    parser.add_argument('--output', default='tiny_book_on_governance_of_machine.pdf',
                        help='Output PDF file path')
    args = parser.parse_args()
    
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
    
    # Write LaTeX to file for debugging
    with open('governance.tex', 'w') as f:
        f.write(latex_content)
    
    # Convert LaTeX to PDF
    print("Converting LaTeX to PDF...")
    latex_to_pdf(latex_content, args.output)


if __name__ == "__main__":
    main()