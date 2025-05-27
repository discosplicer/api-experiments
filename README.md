# project-sunrise

**project-sunrise** is a Python project designed to use the OpenAI API to summarize any text file, no matter how long. It uses an agentic summary inspired by https://github.com/cicero225/llm_pokemon_scaffold to manage an ongoing summary of the current text. The text is processed in chunks of customizable size.

These generated summaries can be read on their own or copied into an LLM in case the original text doesn't fit into the LLM's context (no RAG needed!)

## Features

- Use any OpenAI model (TODO: add Claude and Gemini)
- Summarize plain text files of any length
- Summarize multiple files in a directory (TODO: summarize them all into the same output file)
- Options for chunk size, model, and temperature

## Installation

1. **Clone the repository:**
    ```
    git clone https://github.com/discosplicer/ project-sunrise.git

    cd project-sunrise
    ```

2. **Install dependencies using Poetry**

    `poetry install`

3. Set your OpenAI API key:

    `export OPENAI_API_KEY=your-openai-api-key`

## Usage Example
    ```
    python experiments.py texts/your_text_here.txt --chunk-size 20000 --model o4-mini
    ```

## Limitations
Requires a valid OpenAI API key and internet connection.
API usage may incur costs depending on your OpenAI plan.
The project is in early development; interfaces and features may change.
Not intended for production use without further security and error handling improvements.

## License
MIT License. See LICENSE for details.