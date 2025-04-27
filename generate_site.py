import json
import os
import shutil
from typing import Optional, Dict
import google
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from convert import convert_doc_to_text, convert_doc_to_html, set_docs_service, set_drive_service
import html2text

from doc_list import gdoc_urls


# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/documents.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
]

def get_credentials():
    """Gets valid user credentials from storage.
    
    Returns:
        Credentials, the obtained credential.
    """

    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except google.auth.exceptions.RefreshError as e:
                creds = None
        
        if creds is None:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret_73374229538-l7u9qnk182a3m309ivk097928smmtjjj.apps.googleusercontent.com.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def extract_doc_id(url):
    """Extracts the document ID from a Google Docs URL.
    
    Args:
        url (str): The Google Docs URL
        
    Returns:
        str: The document ID
    """
    # Handle different URL formats
    if '/d/' in url:
        doc_id = url.split('/d/')[1].split('/')[0]
    elif 'id=' in url:
        doc_id = url.split('id=')[1].split('&')[0]
    else:
        raise ValueError(f"Could not extract document ID from URL: {url}")
    return doc_id

def fetch_gdoc(doc_id) -> Optional[dict]:
    """Fetches the content of a Google Doc using the convert module's function.
    
    Args:
        doc_id (str): The ID of the document to fetch
        
    Returns:
        dict: The document represented as a dictionary
    """
    from convert import fetch_gdoc as convert_fetch_gdoc
    return convert_fetch_gdoc(doc_id)

def save_doc(url_names: list[str], doc: dict) -> str:
    txt = convert_doc_to_text(doc)

    for filename in url_names:
        with open(os.path.join("fetched_docs", filename + '.json'), 'w') as f:
            json.dump(doc, f, indent=2)

        with open(os.path.join("fetched_docs", filename + '.txt'), 'w') as f:
            f.write(txt)

    return txt

def convert_html_to_markdown(html_content: str) -> str:
    """Converts HTML content to markdown format.
    
    Args:
        html_content (str): The HTML content to convert
        
    Returns:
        str: The markdown representation of the HTML content
    """
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.escape_snob = True
    h.body_width = 0  # Disable line wrapping
    
    return h.handle(html_content)

with open('post_template.html') as f:
    POST_HTML_TEMPLATE = f.read()

with open('index_template.html') as f:
    INDEX_HTML_TEMPLATE = f.read()

# This function is kept for reference but no longer used
# The functionality has been integrated into the main function with link processing
def save_html(url_names: list[str], gdoc_data: dict) -> tuple[str, str, str]:
    # Get title, description, and HTML content from the Google Doc
    gdoc_title, description, html_content = convert_doc_to_html(gdoc_data)
   
    # Replace placeholders in the HTML template, but don't add the title again
    # since it's already in the HTML content
    html = POST_HTML_TEMPLATE.replace("TITLE", gdoc_title).replace("POST", html_content)
    
    # Write to files
    for filename in url_names:
        with open(os.path.join("posts", filename + ".html"), 'w') as f:
            f.write(html)

    # Use the first url_name as the link to the post
    link = url_names[0] + ".html"

    # Return the HTML title which may include formatting
    # Extract the title from html_content - it should be the first h1 tag
    import re
    html_title = ""
    h1_match = re.search(r'<h1>(.*?)</h1>', html_content)
    if h1_match:
        html_title = h1_match.group(1)
    else:
        # Fallback to gdoc title if no h1 found
        html_title = gdoc_title

    return html_title, description, link

def main(local_only=False):
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
    
    # Create or preserve the posts/images directory
    posts_images_dir = os.path.join('posts', 'images')
    posts_images_existed = os.path.exists(posts_images_dir)
    
    # Save the images directory if it exists
    temp_images = None
    if posts_images_existed:
        import tempfile
        temp_images = tempfile.mkdtemp()
        print(f"Preserving images directory: {posts_images_dir}")
        shutil.copytree(posts_images_dir, os.path.join(temp_images, 'images'))
    
    # Create posts directory if it doesn't exist, otherwise just keep it
    if not os.path.exists('posts'):
        os.makedirs('posts')
    
    # Restore images directory if needed
    if posts_images_existed and temp_images:
        if not os.path.exists(posts_images_dir):
            os.makedirs(posts_images_dir)
        print(f"Restoring images directory to: {posts_images_dir}")
        for item in os.listdir(os.path.join(temp_images, 'images')):
            s = os.path.join(temp_images, 'images', item)
            d = os.path.join(posts_images_dir, item)
            if os.path.isdir(s) and not os.path.exists(d):
                shutil.copytree(s, d)
            elif not os.path.isdir(s) and not os.path.exists(d):
                shutil.copy2(s, d)
        shutil.rmtree(temp_images)
    elif not os.path.exists(posts_images_dir):
        # Create images directory if it didn't exist
        os.makedirs(posts_images_dir)
        
    # Copy the header images to the posts directory
    # Original header
    header_image_path = os.path.join(os.getcwd(), 'liberty_by_design_header.png')
    if os.path.exists(header_image_path):
        print(f"Copying liberty_by_design_header.png to posts directory")
        shutil.copy2(header_image_path, os.path.join('posts', 'liberty_by_design_header.png'))
    
    # Singularity header
    singularity_image_path = os.path.join(os.getcwd(), 'singularity_design_horizontal_strip.png')
    if os.path.exists(singularity_image_path):
        print(f"Copying singularity_design_horizontal_strip.png to posts directory")
        shutil.copy2(singularity_image_path, os.path.join('posts', 'singularity_design_horizontal_strip.png'))

    # Process each document
    documents = {}
    links = []
    
    for url_names, url in gdoc_urls:
        try:
            doc_id = extract_doc_id(url)
            if not doc_id:
                print(f"Failed to extract doc ID from URL: {url}")
                continue
            
            if local_only:
                # Check if cached JSON file exists
                json_path = os.path.join("fetched_docs", url_names[0] + '.json')
                if not os.path.exists(json_path):
                    print(f"Skipping {url_names[0]}: cached document not found at {json_path}")
                    continue
                
                print(f"Using cached version of {url_names[0]}")
                try:
                    with open(json_path, 'r') as f:
                        raw_doc = json.load(f)
                    
                    # Convert the document to HTML using cached document
                    title, description, html_content = convert_doc_to_html(raw_doc)
                    if not html_content:
                        print(f"Failed to convert cached document {json_path} to HTML")
                        continue
                        
                    # Add to documents dictionary
                    documents[url] = url_names[0]
                except Exception as e:
                    print(f"Error processing cached document {json_path}: {str(e)}")
                    continue
            else:
                # Convert the document to HTML with inlined links by fetching from Google
                title, description, html_content = convert_doc_to_html(doc_id)
                if not html_content:
                    print(f"Failed to convert document {doc_id} to HTML")
                    continue
                    
                # Save the raw document for reference
                raw_doc = fetch_gdoc(doc_id)
                documents[url] = save_doc(url_names, raw_doc)
            
            # Create a description block if description exists
            description_html = ""
            if description and description.strip():
                # Convert line breaks to paragraphs
                paragraphs = description.split("<br><br>")
                description_paragraphs = "".join([f"<p>{p}</p>" for p in paragraphs if p.strip()])
                description_html = f'<div class="description-block">{description_paragraphs}</div>'
                
                # Find the first heading and place the description after it
                from bs4 import BeautifulSoup
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
            
            # Save the HTML with links processed and description block
            # Include the header only for the Liberty by Design book
            
            for filename in url_names:
                # For the book, use the template with header; for other posts, remove the header
                # Create PDF download div for liberty_by_design
                pdf_download_html = ''
                if filename == "liberty_by_design":
                    pdf_download_html = '''
<div class="pdf-download">
    <a href="/liberty_by_design.pdf" target="_blank" download>
        <span class="download-icon">📄</span> Download PDF version
    </a>
</div>'''
                    # Add pdf_download_html to the HTML content right after the first h1 header.
                    soup = BeautifulSoup(html_content, 'html.parser')
                    first_h1 = soup.find('div')
                    if first_h1:
                        pdf_div = BeautifulSoup(pdf_download_html, 'html.parser')
                        first_h1.insert_after(pdf_div)
                        # Update the HTML content
                        html_content = str(soup)
                
                if filename == "liberty_by_design":
                    html = POST_HTML_TEMPLATE.replace("TITLE", title).replace("DESCRIPTION_BLOCK", description_html).replace("POST", html_content)
                else:
                    # Remove the header container for non-book blog posts
                    # First extract just the part of the template before the body tag
                    head_part = POST_HTML_TEMPLATE.split("<body>")[0]
                    # Then extract just the container and content part (without the header)
                    body_part = POST_HTML_TEMPLATE.split("<div class=\"container\">")[1]
                    # Combine parts without the header
                    modified_template = head_part + "<body>\n    <div class=\"container\">" + body_part
                    html = modified_template.replace("TITLE", title).replace("DESCRIPTION_BLOCK", description_html).replace("POST", html_content)
                
                with open(os.path.join("posts", filename + ".html"), 'w') as f:
                    f.write(html)
                
                # Convert HTML content to markdown and save to fetched_docs folder
                # Extract just the content part (not the whole template)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                main_content = soup.find('div', id='story')
                if main_content:
                    markdown_content = convert_html_to_markdown(str(main_content))
                    with open(os.path.join("fetched_docs", filename + '.md'), 'w') as f:
                        f.write(markdown_content)
                else:
                    print(f"Could not find main content in {filename}.html to convert to markdown")
            
            # Use the first url_name as the link to the post
            link = url_names[0] + ".html"
            
            # Extract the title from the HTML content for index
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            h1 = soup.find('h1')
            if h1:
                html_title = h1.get_text()
            else:
                # Fallback to gdoc title if no h1 found
                html_title = title
            
            links.append((html_title, description, link))
            
        except Exception as e:
            print(f"Error processing URL {url}: {str(e)}")
    
    # Generate index.html
    links_html = ''
    for title, description, post_url in links:
        links_html += f'''
        <a href="posts/{post_url}" class="post-link">
            <div class="post-title">{title}</div>
            <div class="post-description">{description}</div>
        </a>'''
    index_html = INDEX_HTML_TEMPLATE.replace("LINKS", links_html)
    with open("index.html", 'w') as f:
        f.write(index_html)

    return documents

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate blog site from Google Docs')
    parser.add_argument('--local-only', action='store_true', 
                        help='Use cached documents only without connecting to Google')
    args = parser.parse_args()
    
    try:
        documents = main(local_only=args.local_only)
        if documents:
            print(f"Processed {len(documents)} documents.")
        else:
            print("No documents were processed.")
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
