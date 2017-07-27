import os
import sys
import copy
import pickle
import numpy as np

from gensim.models import Phrases
from gensim.models.phrases import Phraser
from gensim.corpora import Dictionary
from gensim.models import LdaModel

sys.path.append('../preprocess')
from text_cleaner import TextCleaner

class LDACluster:
    """ Latent Dirichlet Allocation: Topic clustering module.
    @param texts: List of plain text, e.g. [['How are you', 'I am fine']]
    @param docs: List of tokenized text, e.g. [['How', 'are', 'you'], ['I', 'am', 'fine']]
    """
    def __init__(self, num_topics=10, no_below=1, no_above=0.5):
        self.num_topics = num_topics
        self.no_below = no_below
        self.no_above = no_above

    def _build_phraser(self, docs):
        # Example: bigram_phraser(['machine', 'learning']) => ['machine_learning']
        self.bigram_phrases = Phrases(docs, min_count=5)
        self.bigram_phraser = Phraser(self.bigram_phrases)

    def _build_vocab(self, docs):
        # Create a dictionary representation of the documents.
        self.vocab = Dictionary(docs)
        # Filter out words that occur less than `no_below` documents, or more than `no_above`% of the documents.
        self.vocab.filter_extremes(no_below=self.no_below, no_above=self.no_above)

    def _append_phrases_to_docs(self, docs):

        new_docs = copy.deepcopy(docs)

        if not hasattr(self, 'bigram_phraser'):
            self._build_phraser(new_docs)

        for i in range(len(new_docs)):
            new_docs[i].extend([token for token in self.bigram_phraser[new_docs[i]] if '_' in token])

        return new_docs

    def preprocess(self, texts):
        # Clean text and append phrases to docs.
        text_cleaner = TextCleaner(filter_sentiment_words=True)
        docs = text_cleaner.clean(texts)
        docs = self._append_phrases_to_docs(docs)
        return docs

    def transform(self, texts, preprocess=True):
        if not hasattr(self, 'model'):
            print('! [LDACluster] Please train model first by calling `fit()`.')
            return

        # Clean text and append phrases to docs.
        if preprocess:
            docs = self.preprocess(texts)
        else:
            docs = texts

        feature_vectors = np.zeros(shape=(len(docs), self.num_topics))

        for i, doc in enumerate(docs):
            # Transform text into the bag-of-words space
            bow_vector = self.model.id2word.doc2bow(doc)
            # Transform into LDA space
            for tup in self.model[bow_vector]:
                feature_vectors[i][tup[0]] = tup[1]

        return feature_vectors

    def fit(self, texts):

        # Clean text and append phrases to docs.
        docs = self.preprocess(texts)

        # Build vocab.
        self._build_vocab(docs)

        # Bag-of-words (word id) representation of the documents.
        corpus = [self.vocab.doc2bow(doc) for doc in docs]

        # Set training parameters.
        num_topics = self.num_topics
        chunksize = 2048
        passes = 20
        iterations = 400
        eval_every = None

        # Train LDA
        print('* [LDA] Training model...')
        self.model = LdaModel(corpus=corpus, id2word=self.vocab, chunksize=chunksize, \
                              alpha='auto', eta='auto', \
                              iterations=iterations, num_topics=num_topics, \
                              passes=passes, eval_every=eval_every)

        self.feature_vectors = self.transform(docs, preprocess=False)
        self.labels = [np.argmax(feature_vector) for feature_vector in self.feature_vectors]

        return self

    def predict(self, texts):
        if not hasattr(self, 'model'):
            print('! [LDACluster] Please train model first by calling `fit()`.')
            return

        feature_vectors = self.transform(texts, preprocess=True)
        labels = [np.argmax(feature_vector) for feature_vector in feature_vectors]

        return labels
