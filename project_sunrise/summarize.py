import argparse
import logging
import os
from dataclasses import dataclass
from typing import List

import dotenv
from openai import OpenAI
from project_sunrise.prompts import (
    META_KNOWLEDGE_PROMPT,
    OPENING_PROMPT,
    META_SUMMARY_PROMPT,
    meta_cleanup_prompt,
)

# Load environment variables from .env file
dotenv.load_dotenv()

@dataclass
class AIModelConfig:
    api_key: str
    model_name: str
    max_tokens: int = 10000
    temperature: float = 1.0


def is_text_file(filename: str, blocksize: int = 512) -> bool:
    """
    This function checks if a file is a text file by attempting to read it.
    It returns True if the file is readable as text, otherwise False.

    TODO: Get python-magic or some other way to not have to look for null bytes,
        which is more of a proxy and not an actual check.
    """
    try:
        with open(filename, "rb") as f:
            chunk = f.read(blocksize)
        # If the chunk contains null bytes, it's likely binary
        if b"\x00" in chunk:
            return False
        # Try decoding as UTF-8
        try:
            chunk.decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False
    except Exception:
        return False


def get_text_files_from_path(path: str) -> List[str]:
    """
    This function returns a list of text files in the given path.
    It filters out non-text files and directories.
    Returns files in alphabetical order.
    """
    if os.path.isfile(path):
        return [path] if is_text_file(path) else []
    files = []
    for root, _, filenames in os.walk(path):
        for fname in filenames:
            full_path = os.path.join(root, fname)
            if is_text_file(full_path):
                files.append(full_path)
    return sorted(files)


def prompt_text_reply(instructions, text, model_conf):
    """
    This function uses the OpenAI API to summarize a text.
    It requires the OpenAI API key and model name to be set in the config.
    """
    # Set a longer timeout since we're using flex.
    openai_client = OpenAI(api_key=model_conf.api_key, timeout=900.0, max_retries=3)
    try:
        response = openai_client.responses.create(
            model=model_conf.model_name,
            input=text,
            instructions=instructions,
            max_output_tokens=model_conf.max_tokens,
            temperature=model_conf.temperature,
        )
        return response.output_text
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "[API ERROR]"


def agentic_summary(chunk, model_conf, bullet_points=None, previous_summary=None):
    prompt = {
        "previous_summary": previous_summary,
        "text": chunk,
    }
    # Prepend the opening prompt if there is no previous summary
    if previous_summary is None:
        meta_prompt = META_KNOWLEDGE_PROMPT + "\n" + OPENING_PROMPT
    else:
        meta_prompt = META_KNOWLEDGE_PROMPT
    new_bullet_points = prompt_text_reply(meta_prompt, str(prompt), model_conf)

    if bullet_points is not None:
        bullet_points += "\n" + new_bullet_points
    else:
        bullet_points = new_bullet_points
    print(f"Raw list of bullet points: {bullet_points}")

    # Add the bullet points to the prompt
    prompt["bullet_points"] = bullet_points

    # Remove previous summary to avoid confusion in the next step
    del prompt["previous_summary"]  

    # Summarize for real
    if previous_summary is not None:
        prompt["text"] = None  # Clear the text to avoid confusion
    new_summary = prompt_text_reply(META_SUMMARY_PROMPT, str(prompt), model_conf)
    print(f"Actual Summary: {new_summary}")

    # Rename to just "summary" for cleanup.
    prompt["summary"] = new_summary

    # Cleanup the bullet points
    cleaned_bullet_points = prompt_text_reply(
        meta_cleanup_prompt(model_conf.max_tokens), str(prompt), model_conf
    )
    print(f"Cleaned up bullet points: {cleaned_bullet_points}")

    return cleaned_bullet_points, new_summary


def summarize_file(input_file: str, model_conf: AIModelConfig, chunk_size: int = 20000):
    text_name = (
        os.path.basename(input_file) if os.path.isfile(input_file) else input_file
    )
    print(f"Starting summarization for {text_name}...")
    # Load the text file
    try:
        with open(input_file, "r", encoding="utf-8") as fr:
            doc = fr.read()
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error opening {input_file}: {e}")
        return
    except Exception as e:
        print(f"Unexpected error reading {input_file}: {e}")
        return
    # 1 OpenAI token is ~4 characters, so we can estimate the number of tokens
    # Use ~5k tokens per chunk so that there is room for other summary text.
    text_length = len(doc)
    bullet_points = None
    previous_summary = None
    for i in range(0, text_length, chunk_size):
        j = min(i + chunk_size, text_length)
        print(
            f"Processing chunk {i // chunk_size + 1}: {doc[i:i+100]}... (length: {len(doc[i:j])})"
        )
        chunk = doc[i:j]
        # Summarize the chunk
        print("Starting summarization process...")
        bullet_points, summarized = agentic_summary(
            chunk,
            model_conf,
            bullet_points=bullet_points,
            previous_summary=previous_summary,
        )
        previous_summary = summarized
    # One last summary pass
    prompt = {
        "text": None,
        "bullet_points": bullet_points,
    }
    summarized = prompt_text_reply(META_SUMMARY_PROMPT, str(prompt), model_conf)
    print(f"Final Summary: {summarized}")
    return summarized, text_name


def main():
    parser = argparse.ArgumentParser(
        description="Project Sunrise: Summarize text/code files using OpenAI API."
    )
    parser.add_argument("input", help="Input file or directory to summarize")
    parser.add_argument("-o", "--output", help="Output file or directory", default=None)
    parser.add_argument(
        "-c", "--chunk-size", type=int, help="Chunk size in characters", default=20000
    )
    parser.add_argument(
        "--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)"
    )
    parser.add_argument("--model", help="OpenAI model name", default="o4-mini")
    parser.add_argument(
        "--max-tokens", type=int, help="Max output tokens", default=10000
    )
    parser.add_argument(
        "--temperature", type=float, help="Sampling temperature", default=1.0
    )
    parser.add_argument(
        "--overall", type=bool, help="whether to produce an overall summary", default=False
    )
    args = parser.parse_args()

    print("overall summary:", args.overall)

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "Error: OpenAI API key must be provided via --api-key or OPENAI_API_KEY environment variable."
        )
        exit(1)

    model_conf = AIModelConfig(
        api_key=api_key,
        model_name=args.model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
    )

    input_files = get_text_files_from_path(args.input)
    if not input_files:
        print("No valid text files found.")
        exit(1)

    if args.overall:
        summaries = []

    for input_file in input_files:
        print(f"Processing file: {input_file}")
        summarized, text_name = summarize_file(
            input_file, model_conf, chunk_size=args.chunk_size
        )
        summarized = f"File {os.path.basename(input_file)} Summarized: \n\n" + summarized
        if not summarized:
            print(f"Failed to summarize {input_file}. Skipping...")
            continue
        if args.overall:
            summaries.append(summarized)
        output_dir = (
            args.output
            if args.output and os.path.isdir(args.output)
            else os.path.dirname(input_file) + "/summaries"
        )
        # Create the directory if it does not exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        output_file = (
            os.path.join(output_dir, f"{text_name}_{model_conf.model_name}.md")
            if args.output is None or os.path.isdir(args.output)
            else args.output
        )
        try:
            # Write the summary to the output file
            with open(output_file, "w", encoding="utf-8") as fw:
                fw.write(summarized)
            print(f"Summarization complete. Check {output_file} for results.")
        except Exception as e:
            print(f"Error writing to {output_file}: {e}")
    if args.overall:
        overall_summary = "\n\n".join(summaries)
        overall_output_file = (
            os.path.join(output_dir, f"overall_summary_{model_conf.model_name}.md")
            if args.output is None or os.path.isdir(args.output)
            else args.output
        )
        try:
            with open(overall_output_file, "w", encoding="utf-8") as fw:
                fw.write(overall_summary)
            folder_summary, _ = summarize_file(overall_output_file, model_conf, chunk_size=args.chunk_size)
            # Overwrite the overall summary with the folder summary
            if folder_summary:
                with open(overall_output_file, "w", encoding="utf-8") as fw:
                    fw.write(folder_summary)
            print(f"Overall summarization complete. Check {overall_output_file} for results.")
        except Exception as e:
            print(f"Error writing overall summary to {overall_output_file}: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    main()
