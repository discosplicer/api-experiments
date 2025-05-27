Here’s a focused MVP todo list for Project Sunrise before publishing on GitHub:

Core Features
* Support Multiple Files:
Add CLI or config to accept multiple file paths or directories.
Recursively detect and load all text/code files in a directory.
Implement file type detection to skip binaries/non-text files.
* Batch Summarization:
Summarize each file individually, then optionally produce a combined summary.
Save per-file and overall summaries to output files.
* Improve Output Structure:
Output summaries in a clear, organized format (e.g., Markdown with file names as headers).
Optionally, print progress and summary stats to the console.
Usability
* Command-Line Interface (CLI):
Add --help and usage instructions.
* Basic Error Handling:
Handle missing files, permission errors, and API failures gracefully.
* Config File Support:
Allow user to specify API keys and model parameters via a config file or environment variables.
Documentation & Cleanup
* README.md:
Project description, installation, usage examples, and limitations.
* Requirements.txt:
List all dependencies.
* Code Cleanup:
Remove unused code, add comments, and ensure consistent formatting.
* Sample Input/Output:
Include example files and expected output for demo purposes.
(Optional for MVP)
* Basic Unit Tests:
Add minimal tests for file detection and CLI argument parsing.
This will make Project Sunrise a functional, demo-ready summarization tool for text/code files.