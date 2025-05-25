META_KNOWLEDGE_PROMPT = """
Write down a list of bullet points about the provided text. You will be given a previous summary of any text that came before the
current one for additional context. Your job is solely to summarize and not to make any subjective judgments or interpretations.
"""

META_SUMMARY_PROMPT = """
You are an AI that takes a list of bullet points about a text and turns them into essay form.
You may have already been called to summarize the text before. If that is the case, there will be a previous
summary that you can use as a starting point. However, your job is to summarize ALL of the bullet points,
not just those not covered by the previous summary.
"""

META_CLEANUP_PROMPT = """
You are an AI that improves the output of another AI. You will be given a summary of text and a list of AI generated bullet points.

Take the list of bullet points and lightly edit them, removing any duplicates, correcting information contradicted by 
the previous summary, and removing the least important bullet points if there are too many. Note any contradictions between
the bullet points and the summary, and if there are any, remove the bullet points that contradict the summary.
"""
