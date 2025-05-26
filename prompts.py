OPENING_PROMPT = """
At the top of the list, write a short paragraph explaining what the document is. Is it code, a book (fiction or non-fiction),
a transcript, a news article, or something else? Include any relevant information that would help generate a summary of the text.
"""

META_KNOWLEDGE_PROMPT = """
Write down a list of bullet points about the provided text. You will be given a previous summary of any text that came before the
current one for additional context. Your job is solely to summarize and not to make any subjective judgments or interpretations.
"""

META_SUMMARY_PROMPT = """
You are an AI that takes a list of bullet points about a text and turns them into a document. This document will be used
in the context for another AI that can't fit the entire original text into its context window, so it should be as information-dense as possible.
However, mostly avoid bullet points in the output document, as this may be confused with the original bullet point list.

You may notice some bullet points have a score and some do not. Be briefer with the bullet points that do not have a score.

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
Remove about 5 percent of the least important bullet points, but do not remove any bullet points that are essential to understanding the text.

If any important information is contained in the summary but not in the bullet points, you may add brief bullet points to cover that information.
"""
