# Jordan's blog

This is a code base for generating a static blog. Blog posts are written in google docs and provided as a list in `doc_list.py`. The code will download the google docs and convert them to HTML, see `generate_site.py` and `convert.py`. Blog posts are rendered using the `post_template.html` template. The landing page is generated using the `index_template.html` template.

After running `generate_site.py`, the blog can be viewed by opening `index.html`. You can also inspect individual posts by opening the corresponding `posts/[post_name].html` file.

# Testing

Run `generate_site.py` to generate the blog. This is fast, so we can use it as the test.

# Best practices

Prefer dataclasses over dicts and tuples for record classes. Always use type hints.

# Git practices

Periodically commit all generated files (blog posts, fetched docs, PDFs) to keep a complete snapshot of the site in the repo. This ensures the site can be recreated exactly as it was at a given point in time.

# PDF Generation

To generate PDF versions of blog posts:
```
python make_governance_pdf.py
```

Required LaTeX packages installation:
```
sudo apt update
sudo apt install -y texlive-latex-base texlive-fonts-recommended texlive-latex-extra
```