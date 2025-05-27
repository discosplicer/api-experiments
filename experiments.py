import argparse
import os

from openai import OpenAI
from secret_api_keys import *
from config import *
from prompts import *

def is_text_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except Exception:
        return False

def get_text_files_from_path(path):
    """
    This function returns a list of text files in the given path.
    It filters out non-text files and directories.
    """
    if os.path.isfile(path):
        return [path] if is_text_file(path) else []
    files = []
    for root, _, filenames in os.walk(path):
        for fname in filenames:
            full_path = os.path.join(root, fname)
            if is_text_file(full_path):
                files.append(full_path)
    return files

def prompt_text_reply(instructions, text):
    """
    This function uses the OpenAI API to summarize a text.
    It requires the OpenAI API key and model name to be set in the config.
    """
    openai_client = OpenAI(api_key=API_OPENAI, timeout=900.0)  # Set a longer timeout for large texts

    response = openai_client.responses.create(
        model=OPENAI_MODEL_NAME,
        input=text,
        instructions=instructions,
        max_output_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        service_tier="flex",
    )
    return response.output_text

def agentic_summary(chunk, bullet_points=None, previous_summary=None):
    prompt = {
        'previous_summary': previous_summary,
        'text': chunk,
    }
    # Prepend the opening prompt if there is no previous summary
    if previous_summary is None:
        meta_prompt = META_KNOWLEDGE_PROMPT + "\n" + OPENING_PROMPT
    else:
        meta_prompt = META_KNOWLEDGE_PROMPT
    response1 = prompt_text_reply(meta_prompt, str(prompt))

    if bullet_points is not None:
        bullet_points += "\n" + response1
    else:
        bullet_points = response1
    print(f"Summary Stage 1: {bullet_points}")
    
    # Add the bullet points to the prompt
    prompt['bullet_points'] = bullet_points

    del prompt['previous_summary']  # Remove previous summary to avoid confusion in the next step

    # Summarize for real
    if previous_summary is not None:
        prompt['text'] = None  # Clear the text to avoid confusion
    response3 = prompt_text_reply(META_SUMMARY_PROMPT, str(prompt))
    print(f"Actual Summary: {response3}")

    # Effectively rename to just "summary" for cleanup.
    prompt['summary'] = response3

    # Cleanup the bullet points
    response2 = prompt_text_reply(META_CLEANUP_PROMPT, str(prompt))
    bullet_points = response2
    print(f"Summary Stage 2: {bullet_points}")

    return bullet_points, response3

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Sunrise: Summarize text/code files using OpenAI API.")
    parser.add_argument("input", help="Input file or directory to summarize")
    parser.add_argument("-o", "--output", help="Output file or directory", default=None)
    parser.add_argument("-c", "--chunk-size", type=int, help="Chunk size in characters", default=20000)
    args = parser.parse_args()
    input_files = get_text_files_from_path(args.input)
    if not input_files:
        print("No valid text files found.")
        exit(1)

    for input_file in input_files:
        text_name = os.path.basename(input_file) if os.path.isfile(input_file) else input_file
        print(f"Starting summarization for {text_name}...")
        # Load the text file
        with open(input_file, "r", encoding="utf-8") as fr:
            doc = fr.read()
        # 1 OpenAI token is ~4 characters, so we can estimate the number of tokens
        # Use ~5k tokens per chunk so that there is room for other summary text.
        text_length = len(doc)
        bullet_points = None
        previous_summary = None
        for i in range(0, text_length, args.chunk_size):
            j = min(i + args.chunk_size, text_length)
            print(f"Processing chunk {i // args.chunk_size + 1}: {doc[i:i+100]}... (length: {len(doc[i:j])})")
            chunk = doc[i:j]
            # Summarize the chunk
            print("Starting summarization process...")
            bullet_points, summarized = agentic_summary(
                chunk,
                bullet_points=bullet_points,
                previous_summary=previous_summary, 
            )
            previous_summary = summarized
        # One last summary pass
        prompt = {
            'text': None,
            'bullet_points': bullet_points,
        }
        summarized = prompt_text_reply(META_SUMMARY_PROMPT, str(prompt))
        print(f"Final Summary: {summarized}")
        output_dir = args.output if args.output and os.path.isdir(args.output) else os.path.dirname(input_file)
        output_file = os.path.join(
            output_dir, f"{text_name}_{OPENAI_MODEL_NAME}.md"
        ) if args.output is None or os.path.isdir(args.output) else args.output
        with open(output_file, "w", encoding="utf-8") as fw:
            fw.write(summarized)
        print(f"Summarization complete. Check {output_file} for results.")