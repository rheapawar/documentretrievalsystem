"""
Build a short, highlighted excerpt of a document showing where the query
matched -- this is what a user actually scans to decide if a result is
relevant, so it matters more to the "feel" of the demo than people expect.

TODO: implement make_snippet(text, query_tokens) -> str

Approach:
  1. Split `text` into words (whitespace-delimited is fine; you don't need
     to re-tokenize with the same regex as tokenizer.py).
  2. Find the position of the FIRST word that matches (case-insensitively,
     stripped of punctuation) any token in query_tokens.
  3. If no match is found, just return the first ~50 words of the text
     as a fallback so you always return *something*.
  4. If a match is found, take a window of ~25 words before and ~25 words
     after that position.
  5. Wrap every word in that window that matches a query token in
     <mark>...</mark> tags (this is what makes it render as highlighted
     in the frontend later).
  6. If you trimmed the start/end of the text, prefix/suffix with "..."
     so it's visually clear this is an excerpt, not the whole document.

Self-check:
    make_snippet("the quick brown fox jumps", ["fox"])
      -> should contain "<mark>fox</mark>" somewhere in the output
    make_snippet("no matches here at all", ["zzz"])
      -> should still return something reasonable, not crash or return ""
"""
import re

WINDOW = 25
delimiter = re.compile(r"[a-z0-9]+")

def make_snippet(text: str, query_tokens: list[str]) -> str:
   if not text or not query_tokens:
        return (text or "")[:160]

   words = re.findall(r'\S+', text)
   lower_words = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in words]
   query_set =  set(query_tokens)

   match_id = next(i for i, w in enumerate(lower_words) if w in query_set), None
   if match_id is None:
        return " ".join(words[: WINDOW * 2])
   
   start = max(0, match_id - WINDOW)
   end = min(len(words), match_id + WINDOW)

   snippets = []
   for i in range(start, end):
      w = words[i]
      if re.sub(r"[^a-z0-9]", "", w.lower()) in query_set:
        w = f"<mark{w}/mark>"
        snippets.append(w)
      else: snippets.append(w)

   prefix = "..." if start != 0 else ""
   suffix = "..." if end != len(words) else ""
   return prefix + " ".join(snippets) + " " + suffix


