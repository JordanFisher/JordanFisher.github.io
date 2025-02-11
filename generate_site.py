import os
import shutil
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

from doc_list import gdoc_urls


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

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
            creds.refresh(Request())
        else:
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

def fetch_document_content(service, doc_id):
    """Fetches the content of a Google Doc and returns it as a string.
    
    Args:
        service: The Google Docs API service instance
        doc_id (str): The ID of the document to fetch
        
    Returns:
        str: The document content as a string
    """
    try:
        document = service.documents().get(documentId=doc_id).execute()
        content = ''
        
        for elem in document.get('body').get('content'):
            if 'paragraph' in elem:
                for para_elem in elem.get('paragraph').get('elements'):
                    if 'textRun' in para_elem:
                        content += para_elem.get('textRun').get('content')
        
        return content
    except Exception as e:
        print(f"Error fetching document {doc_id}: {str(e)}")
        return None

def save_doc(doc: str) -> str:
    title = doc.split('\n')[0].strip()
    filename = title.replace(' ', '_').lower() + '.txt'
    with open(os.path.join("fetched_docs", filename), 'w') as f:
        f.write(doc)
    return doc

with open('post_template.html') as f:
    POST_HTML_TEMPLATE = f.read()

with open('index_template.html') as f:
    INDEX_HTML_TEMPLATE = f.read()

def save_html(doc: str) -> tuple[str, str, str]:
    lines = doc.split('\n')
    title = lines[0].strip()
    
    description = None
    line_index = 1
    while description is None:
        if lines[line_index].strip() != '':
            description = lines[line_index].strip()[1:-1].strip()  # Strip off the surrounding brackets.
            print(description)
            break
        line_index += 1

    filename = title.replace(' ', '_').lower() + '.html'
    post = '\n'.join(f'            <p>{line.strip()}</p>' for line in lines[line_index + 1:] if line.strip() != '')
    html = POST_HTML_TEMPLATE.replace("TITLE", title).replace("POST", post)
    with open(os.path.join("posts", filename), 'w') as f:
        f.write(html)
    return title, description, filename

def main():
    # Get credentials and build service
    creds = get_credentials()
    service = build('docs', 'v1', credentials=creds)
    
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
    for url in gdoc_urls:
        try:
            doc_id = extract_doc_id(url)
            content = fetch_document_content(service, doc_id)
            if content:
                documents[url] = save_doc(content)
                title, description, post_url = save_html(content)
                print("!", description)
                links.append((title, description, post_url))
            else:
                print(f"Failed to fetch content for {url}")
        except ValueError as e:
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
    documents = main()
    print(f"Fetched {len(documents)} documents.")