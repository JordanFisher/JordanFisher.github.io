# Jordan Fisher's Blog

This is a static blog generator for Jordan Ezra Fisher's writings. The blog posts are written in Google Docs and converted to HTML for display.

## Site Generation

To generate the blog, run:

```
python generate_site.py
```

This will fetch the Google Docs listed in `doc_list.py` and convert them to HTML files in the `posts/` directory. The landing page will be generated at `index.html`.

## PDF Generation

To generate a PDF version of the "Tiny Book on Governance of Machine Intelligence" post:

```
# Generate without images (smaller file size)
python make_governance_pdf.py

# Generate with images (larger file size)
python make_governance_pdf.py --include-images

# Custom output file name
python make_governance_pdf.py --output custom_name.pdf
```

The script will:
1. Convert the HTML to LaTeX
2. Generate a PDF file
3. Create a second version with a custom cover ("_with_cover.pdf")

Note that PDF generation requires TeX Live to be installed with additional packages for strikethrough support.

### PDF Templates

Two LaTeX templates are available:
- `latex_templates/a5_booklet_template.tex`: Original A5 format
- `latex_templates/pocket_book_template.tex`: Pocket book format for lulu.com printing (default)

The pocket book template uses:
- Standard dimensions: 17.5cm × 10.8cm
- Professional margins and spacing
- Left-bordered quote styling
- Full text formatting support (including strikethrough in headers)

### Installing TeX Live for PDF Generation

On Ubuntu:

```bash
# Update package lists first
sudo apt update

# Install required LaTeX packages
sudo apt install texlive-latex-base texlive-fonts-recommended texlive-latex-extra
```

If you encounter 404 errors during installation, try:

```bash
sudo apt clean
sudo apt update
sudo add-apt-repository -y universe
sudo apt install -y texlive-latex-base texlive-fonts-recommended texlive-latex-extra
```

If TeX Live is not installed, the script will generate a LaTeX file (`.tex`) but not the PDF.

## Code Structure

Key files and their purposes:

- `doc_list.py`: List of Google Docs to fetch and convert
- `generate_site.py`: Main script to generate the blog
- `convert.py`: Handles conversion of Google Doc JSON to HTML
- `make_governance_pdf.py`: Converts HTML to LaTeX/PDF
- `post_template.html`: Template for individual blog posts
- `index_template.html`: Template for the landing page
- `latex_templates/`: LaTeX templates for PDF generation

## Special Formatting

The HTML to LaTeX conversion preserves:
- Bold, italic, and underlined text
- Strikethrough text (even in headers)
- Lists and nested lists
- Links and references
- Images (when --include-images flag is used)

When making changes to the LaTeX templates, be aware that the PDF generation processes HTML elements in specific ways, particularly for:
1. Section headers with formatting (especially strikethrough)
2. Quote blocks with the fancyquote environment
3. Image inclusion and positioning

## View the Blog

Open `index.html` in a web browser to view the blog.

https://jordanfisher.github.io/
