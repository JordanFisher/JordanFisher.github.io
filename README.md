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
python make_governance_pdf.py
```

This will convert the HTML to LaTeX and then to PDF. Note that this requires TeX Live to be installed.

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

If TeX Live is not installed, the script will generate a LaTeX file (`governance.tex`) but not the PDF.

## View the Blog

Open `index.html` in a web browser to view the blog.

https://jordanfisher.github.io/
