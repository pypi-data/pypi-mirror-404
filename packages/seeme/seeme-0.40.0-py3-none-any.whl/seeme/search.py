import bm25s

def set_up_bm25s_retriever(corpus, text_property:str="text", stopwords="en"):
    if not text_property =="":
        corpus_text = [doc[text_property] for doc in corpus]
    else:
        corpus_text = corpus
    corpus_tokens = bm25s.tokenize(corpus_text, stopwords=stopwords)
    retriever = bm25s.BM25(corpus=corpus)
    retriever.index(corpus_tokens)
    return retriever