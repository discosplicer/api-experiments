OPENING_PROMPT = """
At the top of the list, write a short paragraph explaining what the document is. Is it code, a book (fiction or non-fiction),
a transcript, a news article, or something else? Include any relevant information that would help generate a summary of the text.
Consider why a user would want to feed this text into an LLM, but don't state that explicitly.

This prompt is being called repeatedly on a text that is too long to fit into the context window of another AI. 
If the text appears incomplete, assume what the rest of the text will be and describe that.
Do not use words like "partial", "opening", or "excerpt" in your description, as the full text likely contains the entire work.
"""

META_KNOWLEDGE_PROMPT = """
Write down a list of bullet points about the provided text. You will be given a previous summary of any text that came before the
current one for additional context. Your job is solely to summarize and not to make any subjective judgments or interpretations.

The list of bullet points should be shorter than the previous summary. The previous summary describes the entire original document,
where the text is only a relatively smaller new chunk of the document.
"""

META_SUMMARY_PROMPT = """
You are an AI that takes a list of bullet points about a document and re-writes them in a way that is appropriate for the type of document it is.
For example, if the document is a book, the output should be in essay form. If the document is a codebase, the output should be documentation. This content will be used
as the context for another AI that can't fit the entire original document into its context window, so it should only contain
useful information from the bullet points and should not add judgments or interpretations.
Since this prompt is being called on each section of the text, if you discard any information that is necessary to understand the document it will be permanently lost.

You may notice some bullet points have a score and some do not. The scores represent the importance of the bullet points to the original document,
with (10) being most important and (1) being least important.

Avoid using too many bullet points in the output, as this may be confused with the original bullet point list.
If the output still feels too much like a raw list, try to rewrite a little bit of it to improve the narrative flow and structure,
keeping the context of the original document in mind.
"""

def meta_cleanup_prompt(max_tokens=10000):
    return f"""
    You are an AI that improves the output of another AI. You will be given a summary of text and a list of AI generated bullet points.

    Take the list of bullet points and lightly edit them, removing any duplicates and attempting to resolve contradictions and correct errors.
    Any non-bullet point text above or within the bullet points should be kept but lightly edited, corrected, and moved to the top of the bullet points if needed.

    Give each bullet point a score from (1) to (10) based on how important it is to the overall summary, with (10) being most important and (1) being least important.
    Some bullet points may already have scores; these can be updated if needed but should not change by more than one or two points most of the time.
    Add scores to the bullet points that do not have them using the same scale. Keep the original order of bullet points and DO NOT rank the bullet points by score.

    If any important information is contained in the summary but not in the bullet points, you may add brief bullet points to cover that information.
    These should go in the order that they come up in the summary, and should be given a score with the same scale as the other bullet points.

    This prompt is being called repeatedly on a document that is too long to fit into the context window of another AI. Therefore,
    do not discard any information that is necessary to understand the document, as it will be permanently lost.
    If the output list is likely to exceed or come close to {max_tokens} tokens, consolidate the bullet points with the lowest scores into nearby bullet points,
    or delete them if they are irrelevant to the document as a whole. You can also make any particularly long bullet points more concise.
    If the output list is going to be safely below {max_tokens} tokens, keep the same number of scored bullet points as the input list unless there are any duplicates or contradictions.
    """
