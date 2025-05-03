import os
import shutil
from typing import List, Optional
import google
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request

# Import common functions from generate_site.py
from convert import convert_doc_to_html
from generate_site import (
    get_credentials,
    extract_doc_id,
    fetch_gdoc,
    save_doc,
    convert_html_to_markdown,
    POST_HTML_TEMPLATE,
    set_docs_service,
    set_drive_service
)
from googleapiclient.discovery import build
from liberty_by_design_versions import liberty_versions, BookVersion


def process_book_version(book_version: BookVersion, local_only: bool = False) -> Optional[str]:
    """Process a single book version and generate HTML file.
    
    Args:
        book_version (BookVersion): The book version to process
        local_only (bool): Whether to use local cached files only
        
    Returns:
        Optional[str]: The processed document text or None if failed
    """
    try:
        doc_id = extract_doc_id(book_version.gdoc)
        if not doc_id:
            print(f"Failed to extract doc ID from URL: {book_version.gdoc}")
            return None
        
        if local_only:
            # Check if cached JSON file exists
            import json
            json_path = os.path.join("fetched_docs", book_version.uri + '.json')
            if not os.path.exists(json_path):
                print(f"Skipping {book_version.uri}: cached document not found at {json_path}")
                return None
            
            print(f"Using cached version of {book_version.uri}")
            try:
                with open(json_path, 'r') as f:
                    raw_doc = json.load(f)
                
                try:
                    # Convert the document to HTML using cached document
                    title, description, html_content = convert_doc_to_html(raw_doc)
                    if not html_content:
                        print(f"Failed to convert cached document {json_path} to HTML")
                        return None
                except TypeError:
                    print(f"Error converting {json_path} to HTML: raw document format may be incorrect")
                    return None
            except Exception as e:
                print(f"Error processing cached document {json_path}: {str(e)}")
                return None
        else:
            # Convert the document to HTML with inlined links by fetching from Google
            title, description, html_content = convert_doc_to_html(doc_id)
            if not html_content:
                print(f"Failed to convert document {doc_id} to HTML")
                return None
                
            # Save the raw document for reference
            raw_doc = fetch_gdoc(doc_id)
            save_doc([book_version.uri], raw_doc)
        
        # Create a description block if description exists
        description_html = ""
        if description and description.strip():
            # Convert line breaks to paragraphs
            paragraphs = description.split("<br><br>")
            description_paragraphs = "".join([f"<p>{p}</p>" for p in paragraphs if p.strip()])
            description_html = f'<div class="description-block">{description_paragraphs}</div>'
            
            # Find the first heading and place the description after it
            content_soup = BeautifulSoup(html_content, 'html.parser')
            first_heading = content_soup.find(['h1', 'h2', 'h3'])
            
            if first_heading:
                # Insert the description block after the first heading
                description_div = BeautifulSoup(description_html, 'html.parser')
                first_heading.insert_after(description_div)
                # Update the HTML content
                html_content = str(content_soup)
                # Clear the description_html so it's not added twice
                description_html = ""
        
        # Create PDF download div for the book version
        pdf_download_html = f'''
<div class="pdf-download">
    <a href="/{book_version.uri}.pdf" target="_blank" download>
        <span class="download-icon">📄</span> Download PDF version
    </a>
</div>'''
        
        # Add pdf_download_html to the HTML content right after the first h1 header
        soup = BeautifulSoup(html_content, 'html.parser')
        first_h1 = soup.find('div')
        if first_h1:
            pdf_div = BeautifulSoup(pdf_download_html, 'html.parser')
            first_h1.insert_after(pdf_div)
            # Update the HTML content
            html_content = str(soup)
        
        # Generate the HTML using the template
        html = POST_HTML_TEMPLATE.replace("TITLE", title).replace("DESCRIPTION_BLOCK", description_html).replace("POST", html_content)
        
        # Create posts directory if it doesn't exist
        if not os.path.exists('posts'):
            os.makedirs('posts')
            
        # Write the HTML file
        with open(os.path.join("posts", book_version.uri + ".html"), 'w') as f:
            f.write(html)
        
        # Convert HTML content to markdown and save to fetched_docs folder
        soup = BeautifulSoup(html, 'html.parser')
        main_content = soup.find('div', id='story')
        if main_content:
            markdown_content = convert_html_to_markdown(str(main_content))
            with open(os.path.join("fetched_docs", book_version.uri + '.md'), 'w') as f:
                f.write(markdown_content)
        else:
            print(f"Could not find main content in {book_version.uri}.html to convert to markdown")
            
        print(f"Successfully processed {book_version.uri}")
        return book_version.uri
    
    except Exception as e:
        print(f"Error processing book version {book_version.uri}: {str(e)}")
        return None


def main(local_only=False):
    """Main function to process all book versions."""
    if not local_only:
        # Get credentials and build service
        creds = get_credentials()
        service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Initialize the global docs service and drive service
        set_docs_service(service)
        set_drive_service(drive_service)
        
        # Create fetched_docs directory if it doesn't exist
        if not os.path.exists('fetched_docs'):
            os.makedirs('fetched_docs')
    else:
        print("Running in local-only mode. Will use existing cached documents.")
        # Check if required directories exist
        if not os.path.exists('fetched_docs'):
            print("Error: No cached documents found. Run without --local-only first.")
            return None
    
    # Create posts directory if it doesn't exist
    if not os.path.exists('posts'):
        os.makedirs('posts')
    
    # Copy the header images to the posts directory
    # Original liberty header
    header_image_path = os.path.join(os.getcwd(), 'liberty_by_design_header.png')
    if os.path.exists(header_image_path):
        print(f"Copying liberty_by_design_header.png to posts directory")
        shutil.copy2(header_image_path, os.path.join('posts', 'liberty_by_design_header.png'))
    
    # Singularity header
    singularity_image_path = os.path.join(os.getcwd(), 'singularity_design_horizontal_strip.png')
    if os.path.exists(singularity_image_path):
        print(f"Copying singularity_design_horizontal_strip.png to posts directory")
        shutil.copy2(singularity_image_path, os.path.join('posts', 'singularity_design_horizontal_strip.png'))

    # Process each book version
    processed_versions = []
    for book_version in liberty_versions:
        result = process_book_version(book_version, local_only)
        if result:
            processed_versions.append(result)
    
    return processed_versions


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Liberty by Design book versions')
    parser.add_argument('--local-only', action='store_true', 
                      help='Use cached documents only without connecting to Google')
    args = parser.parse_args()
    
    try:
        processed_versions = main(local_only=args.local_only)
        if processed_versions:
            print(f"Processed {len(processed_versions)} book versions: {', '.join(processed_versions)}")
        else:
            print("No book versions were processed.")
    except google.auth.exceptions.RefreshError as e:
        if not args.local_only:
            print()
            print("You need to re-auth. Trying running these commands:")
            print("  * Make sure you're in the right project, `gcloud config list`, we want `cool-snowfall-429620-i6`")
            print("  * `gcloud auth application-default login`")
            print("  * Delete the `token.pickle` file")
            print("  * Re-run this script")
            print("  * Alternatively, run with --local-only to use cached documents")
            print()
            print()
            print("...")
            print()
            raise e