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
from convert import convert_doc_to_text, convert_doc_to_html, set_docs_service

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

def main():
    # Get credentials and build service
    creds = get_credentials()
    service = build('docs', 'v1', credentials=creds)
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Initialize the global docs service for document fetching
    set_docs_service(service)
        
    # Delete existing fetched_docs and posts directory.
    if os.path.exists('fetched_docs'):
        shutil.rmtree('fetched_docs')
    os.makedirs('fetched_docs')
    if os.path.exists('posts'):
        shutil.rmtree('posts')
    os.makedirs('posts')

    # Process each document
    documents = {}
    links = []
    
    for url_names, url in gdoc_urls:
        try:
            doc_id = extract_doc_id(url)
            if not doc_id:
                print(f"Failed to extract doc ID from URL: {url}")
                continue
                
            # Convert the document to HTML with inlined links
            title, description, html_content = convert_doc_to_html(doc_id)
            if not html_content:
                print(f"Failed to convert document {doc_id} to HTML")
                continue
                
            # Save the raw document for reference
            raw_doc = fetch_gdoc(doc_id)
            documents[url] = save_doc(url_names, raw_doc)
            
            # Save the HTML with links processed
            html = POST_HTML_TEMPLATE.replace("TITLE", title).replace("POST", html_content)
            for filename in url_names:
                with open(os.path.join("posts", filename + ".html"), 'w') as f:
                    f.write(html)
            
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
        <a href="posts/{post_url}" class="story-link">
            <div class="story-title"><h1>{title}</h1></div>
            <div class="story-description">{description}</div>
        </a>'''
    index_html = INDEX_HTML_TEMPLATE.replace("LINKS", links_html)
    with open("index.html", 'w') as f:
        f.write(index_html)

    return documents

if __name__ == '__main__':
    try:
        documents = main()
        print(f"Fetched {len(documents)} documents.")
    except google.auth.exceptions.RefreshError as e:
        print()
        print("You need to re-auth. Trying running these commands:")
        print("  * Make sure you're in the right project, `gcloud config list`, we want `cool-snowfall-429620-i6`")
        print("  * `gcloud auth application-default login`")
        print("  * Delete the `token.pickle` file")
        print("  * Re-run this script")
        print()
        print()
        print("...")
        print()
        raise e
