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


BOOK_TITLE = "Liberty by Design"


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
        html = POST_HTML_TEMPLATE.replace("TITLE", BOOK_TITLE).replace("DESCRIPTION_BLOCK", description_html).replace("POST", html_content)
        
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


def create_merged_version(processed_versions, local_only=False):
    """Create a merged version that combines all book versions with JavaScript switching.
    
    Args:
        processed_versions (list): List of successfully processed book version URIs
        local_only (bool): Whether we're running in local-only mode
    """
    if not processed_versions:
        print("No processed versions to merge.")
        return
    
    print("Creating merged Liberty by Design version with all variants...")
    
    # Find all the HTML files for the processed versions
    version_files = {}
    version_contents = {}
    
    # Map version URIs to their corresponding user_choice values
    version_choices = {version.uri: version.user_choice for version in liberty_versions}
    
    # Read the HTML content from each version
    for version_uri in processed_versions:
        html_path = os.path.join('posts', f"{version_uri}.html")
        if os.path.exists(html_path):
            version_files[version_uri] = html_path
            
            # Read HTML content and extract the story div
            with open(html_path, 'r') as f:
                html_content = f.read()
                
            # Extract content between <div id="story"> and </div>
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            story_div = soup.find('div', id='story')
            
            if story_div:
                # Get the inner HTML of the story div
                version_contents[version_uri] = str(story_div.decode_contents())
            else:
                print(f"Could not find story div in {html_path}")
    
    if not version_contents:
        print("No story content found in processed versions.")
        return
    
    # Read the post template as a base
    with open('post_template.html', 'r') as f:
        template = f.read()
    
    # Create the version selector HTML
    version_selector_html = '''
    <div class="version-selector-container">
        <div class="version-selector">
            <h2>Choose your own adventure</h2>
            <div class="version-options">
    '''
    
    # Add version buttons
    for version_uri in processed_versions:
        if version_uri in version_choices:
            user_choice = version_choices[version_uri]
            is_active = 'active' if version_uri == processed_versions[0] else ''
            button_id = version_uri.replace('liberty_by_design_', '').replace('_version', '')
            if button_id == 'liberty_by_design':
                button_id = 'with_ai_intro'
                
            version_selector_html += f'<button class="version-button {is_active}" data-version="{button_id}">{user_choice}</button>\n'
    
    version_selector_html += '''
            </div>
        </div>
    </div>
    '''
    
    # Create the JavaScript for version switching
    version_script = '''
    <script>
        // Execute immediately instead of waiting for DOMContentLoaded
        (function() {
            // Modify scrollTargetY to scroll to version-selector
            document.addEventListener('DOMContentLoaded', function() {
                // Wait half a second.
                setTimeout(() => {
                    const chevronDown = document.querySelector('.chevron-down-container');
                    if (chevronDown && window.scrollTargetY !== undefined) {
                        // Get position of the chevron-down div.
                        const rect = chevronDown.getBoundingClientRect();
                        const targetY = window.pageYOffset + rect.top;
                        
                        // Update scrollTargetY to just enough to move the chevron-down div
                        // to the very top of the screen.
                        window.scrollTargetY = targetY - (window.innerHeight * 0.01);
                        console.log("Updated scrollTargetY to:", window.scrollTargetY);
                    }
                }, 500);
            });
        
            // Version switching logic
            function setupVersionSelector() {
                const versionButtons = document.querySelectorAll('.version-button');
                const versionContents = document.querySelectorAll('.version-content');
                let currentVersion = '';
                
                function switchToVersion(version, shouldScroll = false) {
                    // Deactivate all buttons and contents
                    versionButtons.forEach(btn => btn.classList.remove('active'));
                    versionContents.forEach(content => content.classList.remove('active'));
                    
                    // Activate the selected version
                    const button = document.querySelector(`.version-button[data-version="${version}"]`);
                    if (button) {
                        button.classList.add('active');
                    }
                    
                    const content = document.getElementById(version);
                    if (content) {
                        content.classList.add('active');
                        
                        // Only scroll if explicitly requested (from button click)
                        if (shouldScroll) {
                            // Scroll to the first title header in the activated version content
                            setTimeout(() => {
                                // Find the first h1 with the title-header class
                                const firstTitleHeader = content.querySelector('h1.title-header');
                                // If title-header not found, try to find the first h1 element
                                const firstHeader = firstTitleHeader || content.querySelector('h1');
                                
                                if (firstHeader) {
                                    // Scroll to position one header height above the header
                                    const headerRect = firstHeader.getBoundingClientRect();
                                    const scrollOffset = headerRect.height; // use 100% of the header's height as offset
                                    const scrollPosition = window.pageYOffset + headerRect.top - scrollOffset;
                                    window.scrollTo({
                                        top: scrollPosition,
                                        behavior: 'smooth'
                                    });
                                } else {
                                    // If no h1 found, scroll to the top of the content
                                    content.scrollIntoView({ behavior: 'smooth' });
                                }
                            }, 50); // Small delay to ensure content is visible
                        }
                    }
                    
                    // Save preference to localStorage
                    localStorage.setItem('preferred_version', version);
                    currentVersion = version;
                    
                    // Handle any anchor in the URL
                    handleAnchorLink();
                }
                
                versionButtons.forEach(button => {
                    button.addEventListener('click', function() {
                        // Clear any hash/anchor from the URL when switching versions
                        if (window.location.hash) {
                            history.pushState("", document.title, window.location.pathname + window.location.search);
                        }
                        const version = this.getAttribute('data-version');
                        // Pass true to indicate we should scroll to the header
                        switchToVersion(version, true);
                        
                        // Prevent default scrolling behavior that might interfere with our custom scrolling
                        return false;
                    });
                });
                
                // Function to handle anchor links
                function handleAnchorLink() {
                    // Check if there's an anchor in the URL
                    if (window.location.hash) {
                        const hash = window.location.hash.substring(1); // Remove the #
                        
                        // Check if this is a prefixed anchor (contains version info)
                        if (hash.includes('-')) {
                            // Extract version from the anchor
                            const parts = hash.split('-');
                            const versionFromAnchor = parts[0];
                            
                            // Switch to that version if needed
                            if (versionFromAnchor !== currentVersion && 
                                document.querySelector(`.version-button[data-version="${versionFromAnchor}"]`)) {
                                switchToVersion(versionFromAnchor, false);
                            }
                            
                            // Scroll to the element
                            setTimeout(() => {
                                const element = document.getElementById(hash);
                                if (element) {
                                    element.scrollIntoView({ behavior: 'smooth' });
                                }
                            }, 100);
                        } else {
                            // For unprefixed anchors, try to find the element in the current version
                            const prefixedAnchor = `${currentVersion}-${hash}`;
                            setTimeout(() => {
                                const element = document.getElementById(prefixedAnchor);
                                if (element) {
                                    element.scrollIntoView({ behavior: 'smooth' });
                                }
                            }, 100);
                        }
                    }
                }
                
                // Listen for hash changes
                window.addEventListener('hashchange', handleAnchorLink);
                
                // Update all anchors in the document to work correctly with the version system
                function updateAnchorsInContent() {
                    // Get all anchor links in the page
                    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                        // Skip links that already include version prefix
                        const href = anchor.getAttribute('href').substring(1);
                        if (!href.includes('-') && href !== '') {
                            // Add click handler to process the anchor
                            anchor.addEventListener('click', function(e) {
                                e.preventDefault();
                                
                                // Create a prefixed anchor for the current version
                                const prefixedAnchor = `${currentVersion}-${href}`;
                                
                                // Find the matching element
                                const targetElement = document.getElementById(prefixedAnchor);
                                if (targetElement) {
                                    // Update the URL hash and scroll to element
                                    history.pushState(null, null, `#${prefixedAnchor}`);
                                    targetElement.scrollIntoView({ behavior: 'smooth' });
                                }
                            });
                        }
                    });
                }
                
                // Add a listener for when versions are changed to update anchors
                versionButtons.forEach(button => {
                    button.addEventListener('click', function() {
                        // Give the DOM time to update
                        setTimeout(updateAnchorsInContent, 200);
                    });
                });
                
                // Check if there's a saved preference
                const savedVersion = localStorage.getItem('preferred_version');
                
                // Use setTimeout to ensure DOM is fully loaded
                setTimeout(() => {
                    if (savedVersion) {
                        switchToVersion(savedVersion, false);
                    } else {
                        // Default to first version if no preference saved
                        const defaultVersion = versionButtons[0].getAttribute('data-version');
                        switchToVersion(defaultVersion, false);
                    }
                }, 100);
                
                // Run once on initial load
                setTimeout(updateAnchorsInContent, 200);
            }
            
            // Check if document is already loaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', setupVersionSelector);
            } else {
                setupVersionSelector();
            }
        })();
    </script>
    '''
    
    # Create CSS for version selector
    version_css = '''
        /* Make the header container take up the full viewport height */
        .above-the-folder {
            min-height: 100vh !important; /* Ensure header fills entire viewport height */
            margin-bottom: 0 !important; /* Remove default margin */
        }

        /* Version selector styling */
        .version-selector-container {
            min-height: 70vh;
        }

        .version-selector {
            margin: 2rem 0;
            padding: 1.5rem;
            margin-top: 0vh;
            background-color: #f8f8f8;
            border-left: 4px solid #0066cc;
            border-radius: 4px;
            transition: all 0.2s ease;
        }
        
        .version-selector h2 {
            margin-top: 0;
            margin-bottom: 1rem;
            font-size: 1.3rem;
        }

        .version-options {
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
        }

        .version-button {
            padding: 0.8rem 1.2rem;
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1.1rem;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: left;
        }

        .version-button:hover {
            background-color: #f0f0f0;
            border-color: #0066cc;
        }

        .version-button.active {
            background-color: #e6f2ff;
            border-color: #0066cc;
            font-weight: 500;
        }

        /* Version content styling */
        .version-content {
            display: none;
        }

        .version-content.active {
            display: block;
        }
        
        /* @media (prefers-color-scheme: dark) { */
            .version-selector {
                background-color: #2a2a2a;
                border-left-color: #5abbff;
            }
            
            .version-button {
                background-color: #333;
                border-color: #555;
                color: #f0f0f0;
            }
            
            .version-button:hover {
                background-color: #444;
                border-color: #5abbff;
            }
            
            .version-button.active {
                background-color: #1e3a50;
                border-color: #5abbff;
            }
        /* } */
    '''
    
    # Create version content divs and prefix all anchor IDs with version name
    version_divs = ''
    for version_uri in processed_versions:
        button_id = version_uri.replace('liberty_by_design_', '').replace('_version', '')
        if button_id == 'liberty_by_design':
            button_id = 'with_ai_intro'
            
        # Parse the content with BeautifulSoup to modify IDs
        soup = BeautifulSoup(version_contents[version_uri], 'html.parser')
        
        # Find all elements with ID attributes and prefix them with the button_id
        for element in soup.find_all(id=True):
            if element.get('id') != button_id:  # Don't modify the main version div ID
                original_id = element.get('id')
                # Create a prefixed ID to avoid conflicts
                prefixed_id = f"{button_id}-{original_id}"
                element['id'] = prefixed_id
                
                # Also update any anchor links that point to this ID within this version
                for anchor in soup.find_all('a', href=f"#{original_id}"):
                    anchor['href'] = f"#{prefixed_id}"
        
        is_active = 'active' if version_uri == processed_versions[0] else ''
        version_divs += f'<div id="{button_id}" class="version-content {is_active}">{soup.decode_contents()}</div>\n'
    
    # Inject CSS into template head
    template = template.replace('</style>', version_css + '\n    </style>')
    
    # Prepare the content to replace in the template
    content_to_inject = f"{version_selector_html}\n{version_divs}"
    merged_html = template.replace("TITLE", BOOK_TITLE).replace('DESCRIPTION_BLOCK', '').replace('POST', content_to_inject)

    # Add the version switching script before the closing body tag
    merged_html = merged_html.replace('</body>', f'{version_script}\n</body>')
    
    # Write to the merged version file
    merged_path = os.path.join('posts', 'liberty_by_design.html')
    with open(merged_path, 'w') as f:
        f.write(merged_html)
    
    print(f"Created merged version at {merged_path}")


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
    
    # Create a merged version with JavaScript for version switching
    create_merged_version(processed_versions, local_only)
    
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