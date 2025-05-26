META_KNOWLEDGE_PROMPT = """
Write down a list of bullet points about the provided text. You will be given a previous summary of any text that came before the
current one for additional context. Your job is solely to summarize and not to make any subjective judgments or interpretations.

At the top of the list, write a short paragraph explaining what the document is. Is it code, a book (fiction or non-fiction),
a transcript, a news article, or something else? Include any relevant information that would help generate a summary of the text.
"""

META_SUMMARY_PROMPT = """
You are an AI that takes a list of bullet points about a text and turns them into a document. This document will be used
in the context for another AI that can't fit the entire original text into its context window, so it should be as information-dense as possible.
However, mostly avoid bullet points in the output document, as this may be confused with the original bullet point list.

If any information is given outside of the bullet points, it should only be included at the top of the output document.

You may have already been called to summarize the text before. If that is the case, there will be a previous
summary that you can use as a starting point. However, your job is to summarize ALL of the bullet points,
not just those not covered by the previous summary. Do not mention the existence of the previous summary in your output.
"""

META_CLEANUP_PROMPT = """
You are an AI that improves the output of another AI. You will be given a summary of text and a list of AI generated bullet points.

Take the list of bullet points and lightly edit them, removing any duplicates, attempting to resolve contradictions, and removing the least important bullet points.
Any non-bullet point summary text should be moved to the top of the list and de-duplicated.

Bullet points that are later in the list are less likely to be important than bullet points earlier in the list,
but this is not always the case. You should use your judgment to determine which bullet points are most important.

If any important information is contained in the summary but not in the bullet points, you may add brief bullet points to cover that information.
"""
