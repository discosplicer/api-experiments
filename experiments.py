from openai import OpenAI
from secret_api_keys import *
from config import *
from prompts import *

def prompt_text_reply(instructions, text):
    """
    This function uses the OpenAI API to summarize a text.
    It requires the OpenAI API key and model name to be set in the config.
    """
    openai_client = OpenAI(api_key=API_OPENAI)

    response = openai_client.responses.create(
        model=OPENAI_MODEL_NAME,
        input=text,
        instructions=instructions,
        max_output_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )
    return response.output_text

def agentic_summary(chunk, bullet_points=None, previous_summary=None):
    prompt = {
        'text': chunk,
        'previous_summary': previous_summary
    }
    response1 = prompt_text_reply(META_KNOWLEDGE_PROMPT, str(prompt))

    if bullet_points is not None:
        bullet_points += response1
    else:
        bullet_points = response1
    print(f"Summary Stage 1: {bullet_points}")
    
    # Add the bullet points to the prompt
    prompt['bullet_points'] = bullet_points
    # Cleanup the bullet points
    response2 = prompt_text_reply(META_CLEANUP_PROMPT, str(prompt))
    bullet_points = response2
    prompt['bullet_points'] = bullet_points
    print(f"Summary Stage 2: {bullet_points}")

    # Summarize for real
    response3 = prompt_text_reply(META_SUMMARY_PROMPT, str(prompt))
    print(f"New Prompt: {response3}")

    return bullet_points, response3

if __name__ == "__main__":
    with open("texts/cr_s1e1.txt", "r", encoding="utf-8") as fr:
        doc = fr.read()
    # 1 OpenAI token is ~4 characters, so we can estimate the number of tokens
    text_length = len(doc)
    bullet_points = None
    previous_summary = None
    for i in range(0, text_length, 40000):
        j = min(i + 40000, text_length)
        print(f"Processing chunk {i // 40000 + 1}: {doc[i:i+100]}... (length: {len(doc[i:j])})")
        chunk = doc[i:j]
        # Summarize the chunk
        print("Starting summarization process...")
        bullet_points, summarized = agentic_summary(
            chunk,
            bullet_points=bullet_points,
            previous_summary=previous_summary, 
        )
        previous_summary = summarized
    with open("agentic_summary.txt", "w", encoding="utf-8") as fw:
        fw.write(summarized)
    # with open("agentic_prompt.txt", "w", encoding="utf-8") as fw:
    #     fw.write(customized_prompt)
    print("Summarization complete. Check agentic_summary.txt for results.")