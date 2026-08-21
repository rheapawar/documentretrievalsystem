import re

WINDOW = 25
delimiter = re.compile(r"[a-z0-9]+")

def make_snippet(text: str, query_tokens: list[str]) -> str:
   if not text or not query_tokens:
        return (text or "")[:160]

   words = re.findall(r'\S+', text)
   lower_words = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in words]
   query_set =  set(query_tokens)

   match_id = next((i for i, w in enumerate(lower_words) if w in query_set), None)
   if match_id is None:
      return " ".join(words[: WINDOW * 2])
   
   start = max(0, match_id - WINDOW)
   end = min(len(words), match_id + WINDOW)

   snippets = []
   for i in range(start, end):
      w = words[i]
      stripped = lower_words[i]
      if stripped in query_set:
        snippets.append(f"<mark>{w}</mark>")
      else: snippets.append(w)

   prefix = "..." if start != 0 else ""
   suffix = "..." if end != len(words) else ""
   return prefix + " ".join(snippets) + " " + suffix


