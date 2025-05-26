from openai import OpenAI
from secret_api_keys import *
from config import *
from prompts import *

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
        'text': chunk,
        'previous_summary': previous_summary
    }
    # Prepend the opening prompt if there is no previous summary
    if previous_summary is None:
        meta_prompt = OPENING_PROMPT + "\n" + META_KNOWLEDGE_PROMPT
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

    # Summarize for real
    prompt['text'] = None  # Clear the text to avoid confusion
    response3 = prompt_text_reply(META_SUMMARY_PROMPT, str(prompt))
    print(f"Actual Summary: {response3}")

    prompt['summary'] = response3
    del prompt['previous_summary']  # Clear previous summary to avoid confusion

    # Cleanup the bullet points
    response2 = prompt_text_reply(META_CLEANUP_PROMPT, str(prompt))
    bullet_points = response2
    print(f"Summary Stage 2: {bullet_points}")

    return bullet_points, response3

if __name__ == "__main__":
    text_name = "pokemon_agent"
    print(f"Starting summarization for {text_name}...")
    # Load the text file
    with open(f"texts/{text_name}.txt", "r", encoding="utf-8") as fr:
        doc = fr.read()
    # 1 OpenAI token is ~4 characters, so we can estimate the number of tokens
    # Use ~5k tokens per chunk so that there is room for other summary text.
    text_length = len(doc)
    bullet_points = None
    previous_summary = None
    for i in range(0, text_length, 20000):
        j = min(i + 20000, text_length)
        print(f"Processing chunk {i // 20000 + 1}: {doc[i:i+100]}... (length: {len(doc[i:j])})")
        chunk = doc[i:j]
        # Summarize the chunk
        print("Starting summarization process...")
        bullet_points, summarized = agentic_summary(
            chunk,
            bullet_points=bullet_points,
            previous_summary=previous_summary, 
        )
        previous_summary = summarized
    with open(f"{text_name}_{OPENAI_MODEL_NAME}.md", "w", encoding="utf-8") as fw:
        fw.write(summarized)
    print("Summarization complete. Check {text_name}.md for results.")