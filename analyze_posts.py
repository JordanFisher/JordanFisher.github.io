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
client = AsyncAnthropic(api_key=api_key, timeout=15 * 60)

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
        
        # Truncate content if it's too long.
        max_length = 40_000
        if len(content) > max_length:
            logger.warning(f"Content length exceeds {max_length} characters, truncating...")
            content = content[:max_length] + " ... [truncated content, don't worry about analyzing this sentence]"

        # Call Claude with the content
        message = await client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=48_000,
            thinking={
                "type": "enabled",
                "budget_tokens": 32_000,
            },
            temperature=1,
            system="""Review the user's writing for spelling mistakes and grammatical mistakes. For each mistake, write the original sentence as `Original: <original sentence>`, and then provide the corrected sentence as `Corrected: <corrected sentence>`. Do not provide any other information such as suggestions about content. For sentences that don't have mistakes, don't output anything. If there aren't any mistakes anywhere, return a happy emoji and a congratulations.

Style guide:
* Prefer fewer periods when possible, for example `vs` instead of `vs.`
* When an em dash is seperating two clauses or sentences, there should be a space around both sides of the em dash, ie, this is good: `this is a sentence — and so is this.`
* If there are two em dashes surrounding what could be a clause or a parenthetical phrase, there should be no space after the first em dash and before the second em dash, ie, this is good: `the large mountain —which was very tall— was called Mt Fuji`.
* If you have a suggestion about an em dash, read the two previous em dash guidelines carefully and make sure your suggestion is correct.
* For example `we assume—optimistically—that this is true` is incorrect, because the em dash is surrounding a short phrase or clause. The correct version is `we assume —optimistically— that this is true`.
* If a sentence is slightly casual, but still correct, it's fine to keep it as is.
* The words executive, legislature, and judiciary should be lowercase when used in a sentence, unless they are at the beginning of a sentence.
* If there is a space after the end of a markdown italic tag, you can ignore it. For example `_this is italic_ .` is fine, even though it has an erroneous space. If you see extra spaces elsewhere before punctuation, please correct it.
* If you see \\( or \\), assume these are just normal parentheses and ignore the backslashes.

Form all of your corrections within your thinking. Then, while still thinking, review each suggestion, and make sure to check that your corrections are correct and follow the above style guide. If the correction is the same as the original, don't output anything. If you see a sentence that is correct, but could be improved, don't output anything. If you see a sentence that is incorrect, but could be improved, don't output anything. If you see a sentence that is incorrect, and could be improved, don't output anything. If you see a sentence that is correct, and could be improved, don't output anything. If you see a sentence that is incorrect, and could not be improved, don't output anything. If you see a sentence that is correct, and could not be improved, don't output anything. If you see a sentence that is incorrect, and could not be improved, don't output anything. If you see a sentence that is correct, and could not be improved, don't output the suggestion. Finally, after thinking, list out your corrections. Please, please, please be extra careful to follow the em dash style, it is a little different than your typical style.""",
            messages=[
                {"role": "user", "content": content}
            ]
        )

        analysis_result = message.content[-1].text
        
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
    
    # Create tasks but limit concurrency to avoid rate limits
    # Process in smaller batches of 3 at a time
    batch_size = 3
    results = []
    
    for i in range(0, len(md_files), batch_size):
        batch = md_files[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} of {(len(md_files) + batch_size - 1) // batch_size}")
        
        tasks = [analyze_post(file_path) for file_path in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        results.extend(batch_results)
        
        # Add a small delay between batches to be nicer to the API
        if i + batch_size < len(md_files):
            logger.info(f"Waiting 2 seconds before next batch...")
            await asyncio.sleep(2)
    
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