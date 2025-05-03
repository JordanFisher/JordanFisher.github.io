# Jordan Fisher's Blog

This is a static blog generator for Jordan Ezra Fisher's writings. The blog posts are written in Google Docs and converted to HTML for display.

## Site Generation

To generate the blog, run:

```
python generate_site.py
```

This will fetch the Google Docs listed in `posts.py` and convert them to HTML files in the `posts/` directory. The landing page will be generated at `index.html`.

**IMPORTANT**: Do not manually edit `index.html` as it's a generated file. Any changes made directly to it will be overwritten the next time `generate_site.py` is run. Instead, modify the content in `posts.py` and the templates in `index_template.html` and `post_template.html`.

## Book Generation

To generate the Liberty by Design book in multiple versions:

```bash
# Generate all versions of the book
python make_governance.py

# Use only local cached documents without fetching from Google Docs
python make_governance.py --local-only
```

## PDF Generation

To generate a PDF version of Liberty by Design books:

```bash
# Generate without images (smaller file size)
python make_governance_pdf.py

# Generate with images (larger file size)
python make_governance_pdf.py --include-images

# Custom output file name
python make_governance_pdf.py --output custom_name.pdf

# Skip site generation step (use when HTML is up-to-date)
python make_governance_pdf.py --skip-site-generation

# Regenerate PDF from existing LaTeX without regenerating site or LaTeX 
# (fastest option for iterating on LaTeX formatting)
python make_governance_pdf.py --pdf-only
```

The script will:
1. Generate the site first (unless --skip-site-generation is used)
2. Convert the HTML to LaTeX
3. Generate a PDF file
4. Create a second version with a custom cover ("_with_cover.pdf")

### PDF Generation Workflow Tips

When working on PDF styling:

1. For quick iterations on LaTeX formatting:
   - Edit the .tex file directly
   - Run `python make_governance_pdf.py --pdf-only` to see the changes
   - This bypasses the site generation and HTML-to-LaTeX conversion steps

2. Chapter numbers in inlined documents:
   - The HTML version displays chapter numbers with custom CSS styling
   - The PDF version uses sans-serif italic small font for chapter numbers
   - To modify styling, edit the inline_links function in convert.py (for HTML) 
     or make_governance_pdf.py (for LaTeX)

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

- `posts.py`: List of blog posts to fetch and convert
- `liberty_by_design_versions.py`: List of Liberty by Design book versions
- `generate_site.py`: Main script to generate the blog
- `make_governance.py`: Script to generate different versions of the Liberty by Design book
- `convert.py`: Handles conversion of Google Doc JSON to HTML and inlines nested documents with chapter numbering
- `make_governance_pdf.py`: Converts HTML to LaTeX/PDF with LaTeX-specific formatting
- `analyze_posts.py`: Analyzes markdown versions of posts for spelling and grammar using Anthropic's Claude
- `post_template.html`: Template for individual blog posts (includes CSS for chapter numbers)
- `index_template.html`: Template for the landing page
- `latex_templates/`: LaTeX templates for PDF generation
- `requirements.txt`: List of Python dependencies required for the project

### Important Functions

- `convert.py:inline_links()`: Handles inlining of linked Google Docs as chapters with sequential numbering
- `make_governance_pdf.py:html_to_latex()`: Converts HTML to LaTeX, including chapter number formatting
- `make_governance_pdf.py:process_inline_elements()`: Preserves text formatting (bold, italic, etc.) when converting to LaTeX

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

## Dependency Management

This project uses various Python libraries to handle different aspects of the blog generation and analysis. All required dependencies are listed in `requirements.txt`. To install them:

```bash
pip install -r requirements.txt
```

### Important Note

When adding new functionality that requires installing new Python packages, always update the `requirements.txt` file to ensure other contributors can easily set up their environment:

```bash
# After installing a new package:
pip freeze | grep package-name >> requirements.txt
# Or manually add the package name to requirements.txt
```

## Content Analysis

The `analyze_posts.py` script uses Anthropic's Claude API to analyze the markdown versions of blog posts for spelling and grammar mistakes. To use it:

1. Store your Anthropic API key in `~/.config/blog_analyzer/config.env` using the format:
   ```
   ANTHROPIC_API_KEY="your-api-key-here"
   ```
   
2. Run the script:
   ```bash
   python analyze_posts.py
   ```

3. Analysis results will be saved to the `analysis/` directory with one file per post.

## Using Claude Code

[Claude Code](https://claude.ai/code) is integrated with this repository to assist with development and content generation. Claude Code can:

- Update site templates and styling
- Modify PDF generation code
- Debug issues with site generation
- Help analyze and process Google Doc content

When using Claude Code with this repository:
- It will automatically run `generate_site.py` when executing `make_governance_pdf.py`
- It understands the blog structure and can help modify templates
- It can assist with LaTeX formatting issues

To use Claude Code effectively:
1. Ask it to examine specific files or components
2. Provide clear requirements when making changes
3. Have it run `generate_site.py` to test changes to templates or converters

## View the Blog

Open `index.html` in a web browser to view the blog.

https://jordanfisher.github.io/