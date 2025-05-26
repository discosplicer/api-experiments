OPENING_PROMPT = """
At the top of the list, write a short paragraph explaining what the document is. Is it code, a book (fiction or non-fiction),
a transcript, a news article, or something else? Include any relevant information that would help generate a summary of the text.
Consider why a user would want to feed this text into an LLM, but don't state that explicitly.

This prompt is being called repeatedly on a text that is too long to fit into the context window of another AI. 
If the text appears incomplete, assume what the rest of the text will be and describe that. Do not use words like "partial" or "excerpt" in your description.
"""

META_KNOWLEDGE_PROMPT = """
Write down a list of bullet points about the provided text. You will be given a previous summary of any text that came before the
current one for additional context. Your job is solely to summarize and not to make any subjective judgments or interpretations.

This prompt is being called repeatedly on a text that is too long to fit into the context window of another AI. Therefore,
do not discard any information that is necessary to understand the text, as it will be permanently lost.
"""

META_SUMMARY_PROMPT = """
You are an AI that takes a list of bullet points about a text and turns them into a document. This document will be used
in the context for another AI that can't fit the entire original text into its context window, so it should be as information-dense as possible.
This prompt is being called repeatedly on a text that is too long to fit into the context window of another AI. Therefore,
do not discard any information that is necessary to understand the text, as it will be permanently lost.
However, mostly avoid bullet points in the output document, as this may be confused with the original bullet point list.

You may notice some bullet points have a score and some do not. If so, be briefer with the bullet points that do not have a score.

You may have already been called to summarize the text before. If that is the case, there will be a previous
summary that you can use as a starting point. However, your job is to summarize ALL of the bullet points,
not just those not covered by the previous summary. Do not mention the existence of the previous summary in your output.
"""

META_CLEANUP_PROMPT = """
You are an AI that improves the output of another AI. You will be given a summary of text and a list of AI generated bullet points.

Take the list of bullet points and lightly edit them, removing any duplicates and attempting to resolve contradictions and correct errors.
Any non-bullet point text above or within the bullet points should be kept but lightly edited, corrected, and moved to the top of the bullet points if needed.

Give each bullet point a score from (1) to (10) based on how important it is to the overall summary, with (10) being most important and (1) being least important.
Some bullet points may already have scores; these can be updated if needed but should not change by more than one or two points most of the time.
Bullet points with a low score should be consolidated into other bullet points, being careful not to delete critical information.
Order the new bullet points by the order that they come up in the summary, and DO NOT rank them by score.

If any important information is contained in the summary but not in the bullet points, you may add brief bullet points to cover that information.
These should go in the order that they come up in the summary, and should be given a score with the same scale as the other bullet points.

This prompt is being called repeatedly on a text that is too long to fit into the context window of another AI. Therefore,
do not discard any information that is necessary to understand the text, as it will be permanently lost.
"""
