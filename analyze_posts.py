#!/usr/bin/env python3
import os
import glob
import asyncio
import time
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load API key from config file
config_path = os.path.expanduser("~/.config/blog_analyzer/config.env")
if not os.path.exists(config_path):
    raise FileNotFoundError(f"Config file not found at {config_path}")

load_dotenv(config_path)
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

# Initialize the Anthropic client
client = AsyncAnthropic(api_key=api_key)

async def analyze_post(file_path):
    """
    Analyze a markdown file for spelling and grammar errors using Claude
    
    Args:
        file_path (str): Path to the markdown file
    
    Returns:
        str: The analysis result from Claude
    """
    start_time = time.time()
    post_name = os.path.basename(file_path).replace(".md", "")
    logger.info(f"Analyzing post: {post_name}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Call Claude with the content
        message = await client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            system="Review the user's writing and highlight spelling mistakes and grammatical mistakes.",
            messages=[
                {"role": "user", "content": content}
            ]
        )
        
        analysis_result = message.content[0].text
        
        # Save the result
        output_file = os.path.join("analysis", f"{post_name}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(analysis_result)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Completed analysis of {post_name} in {elapsed_time:.2f} seconds")
        
        return f"Analysis of {post_name} completed"
    
    except Exception as e:
        logger.error(f"Error analyzing {post_name}: {str(e)}")
        return f"Error analyzing {post_name}: {str(e)}"

async def main():
    """
    Main function to analyze all markdown posts in parallel
    """
    # Ensure analysis directory exists
    os.makedirs("analysis", exist_ok=True)
    
    # Get all markdown files
    md_files = glob.glob("fetched_docs/*.md")
    
    if not md_files:
        logger.warning("No markdown files found in fetched_docs/ directory")
        return
    
    # For testing, uncomment the next line to process only one file
    # md_files = [md_files[0]]
    
    logger.info(f"Found {len(md_files)} markdown files to analyze")
    
    # Create tasks for analyzing each post in parallel
    tasks = [analyze_post(file_path) for file_path in md_files]
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Log results
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Task failed with error: {result}")
        else:
            logger.info(result)
    
    logger.info("All analyses completed")

if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())