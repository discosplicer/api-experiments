import argparse
import logging
import os
from dataclasses import dataclass
from typing import List

from openai import OpenAI
from project_sunrise.prompts import (
    META_KNOWLEDGE_PROMPT,
    OPENING_PROMPT,
    META_SUMMARY_PROMPT,
    META_CLEANUP_PROMPT,
)


@dataclass
class AIModelConfig:
    api_key: str
    model_name: str
    max_tokens: int = 10000
    temperature: float = 1.0


def is_text_file(filename: str) -> bool:
    """
    This function checks if a file is a text file by attempting to read it.
    It returns True if the file is readable as text, otherwise False.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            f.read(1024)
        return True
    except Exception:
        return False


def get_text_files_from_path(path: str) -> List[str]:
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


def prompt_text_reply(instructions, text, model_conf):
    """
    This function uses the OpenAI API to summarize a text.
    It requires the OpenAI API key and model name to be set in the config.
    """
    openai_client = OpenAI(
        api_key=model_conf.api_key, timeout=900.0
    )  # Set a longer timeout for large texts
    try:
        response = openai_client.responses.create(
            model=model_conf.model_name,
            input=text,
            instructions=instructions,
            max_output_tokens=model_conf.max_tokens,
            temperature=model_conf.temperature,
            service_tier="flex",
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
    response1 = prompt_text_reply(meta_prompt, str(prompt), model_conf)

    if bullet_points is not None:
        bullet_points += "\n" + response1
    else:
        bullet_points = response1
    print(f"Summary Stage 1: {bullet_points}")

    # Add the bullet points to the prompt
    prompt["bullet_points"] = bullet_points

    del prompt[
        "previous_summary"
    ]  # Remove previous summary to avoid confusion in the next step

    # Summarize for real
    if previous_summary is not None:
        prompt["text"] = None  # Clear the text to avoid confusion
    response3 = prompt_text_reply(META_SUMMARY_PROMPT, str(prompt), model_conf)
    print(f"Actual Summary: {response3}")

    # Effectively rename to just "summary" for cleanup.
    prompt["summary"] = response3

    # Cleanup the bullet points
    response2 = prompt_text_reply(META_CLEANUP_PROMPT, str(prompt), model_conf)
    bullet_points = response2
    print(f"Summary Stage 2: {bullet_points}")

    return bullet_points, response3


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
    args = parser.parse_args()

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

    for input_file in input_files:
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
            continue
        except Exception as e:
            print(f"Unexpected error reading {input_file}: {e}")
            continue
        # 1 OpenAI token is ~4 characters, so we can estimate the number of tokens
        # Use ~5k tokens per chunk so that there is room for other summary text.
        text_length = len(doc)
        bullet_points = None
        previous_summary = None
        for i in range(0, text_length, args.chunk_size):
            j = min(i + args.chunk_size, text_length)
            print(
                f"Processing chunk {i // args.chunk_size + 1}: {doc[i:i+100]}... (length: {len(doc[i:j])})"
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
        summarized = prompt_text_reply(META_SUMMARY_PROMPT, str(prompt))
        print(f"Final Summary: {summarized}")
        output_dir = (
            args.output
            if args.output and os.path.isdir(args.output)
            else os.path.dirname(input_file)
        )
        output_file = (
            os.path.join(output_dir, f"{text_name}_{model_conf.model_name}.md")
            if args.output is None or os.path.isdir(args.output)
            else args.output
        )
        try:
            with open(output_file, "w", encoding="utf-8") as fw:
                fw.write(summarized)
            print(f"Summarization complete. Check {output_file} for results.")
        except Exception as e:
            print(f"Error writing to {output_file}: {e}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    main()
