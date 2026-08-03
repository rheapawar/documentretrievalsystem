from collections import defaultdict

class InvertedIndex:
    def __init__(self):
        self.listings : defaultdict[str, dict[str, int]] = defaultdict(dict)
        self.doc_lengths : dict[str, int] = {}

    @property
    def doc_count(self) -> int:
        return len(self.doc_lengths)

    @property
    def avg_doc_length(self) -> float:
        if not self.doc_lengths:
            return 0.0
        return sum(self.doc_lengths.values())/self.doc_count


    def add_document(self, doc_id: str, tokens: list[str]) -> None:
        if doc_id in self.doc_lengths:
            self.remove_document(doc_id)
        for token in tokens:
            self.listings[token][doc_id] = self.listings[token].get(doc_id, 0) + 1
        self.doc_lengths [doc_id] = len(tokens)

    def remove_document(self, doc_id: str) -> None:
        for innerdict in self.listings.values():
            innerdict.pop(doc_id, None)
        self.doc_lengths.pop(doc_id, None)
            

    def document_frequency(self, token: str) -> int:
        return len(self.listings.get(token, {}))

    def term_frequency(self, token: str, doc_id: str) -> int:
        return self.listings.get(token, {}).get(doc_id, 0)

    def documents_containing(self, token: str) -> list[str]:
        return list(self.listings.get(token, {}).keys())
