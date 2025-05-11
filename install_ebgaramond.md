# Installing EB Garamond LaTeX Package

To install the EB Garamond font for LaTeX, follow these steps:

1. Install the texlive-fonts-extra package which contains the EB Garamond LaTeX font:
   ```
   sudo apt-get install texlive-fonts-extra
   ```

2. Verify the installation:
   ```
   kpsewhich ebgaramond.sty
   ```
   This should return the path to the ebgaramond.sty file if it's installed correctly.

3. Refresh the TeX database if needed:
   ```
   sudo texhash
   ```

4. You can also install the system font for better rendering:
   ```
   sudo apt-get install fonts-ebgaramond
   ```

These steps should properly install the EB Garamond font for use with LaTeX.