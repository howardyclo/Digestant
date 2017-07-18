import sys
import numpy as np
import pandas as pd
import spacy

from datetime import date

sys.path.append('../data_helpers/')
from twitter_data_helper import TwitterDataHelper
from reddit_data_helper import RedditDataHelper
from data_aggregator import DataAggregator

from sklearn import metrics
from sklearn.cluster import KMeans

print('* Loading SpaCy "en_core_web_md" corpus...')
nlp = spacy.load('en_core_web_md')
print('* Success.')
print('-'*116)

class Cluster(object):
    def __init__(self):
        self.best_score = 0
        self.best_cluster_model = None

    def _unwanted_token(self, token, languages=['en'], filter_stopwords=True, filter_url=True, filter_non_alpha=True):
        """ Unwanted token conditions for `preprocessing()` """
        if languages and token.lang_ not in languages:
            return True
        if filter_stopwords and token.is_stop:
            return True
        if filter_url and token.like_url:
            return True
        if filter_non_alpha and not token.is_alpha:
            return True
        if token.text.lower() == 'rt':
            return True
        return False

    def preprocess(self, df):

        try: texts = df['text']
        except: texts = []

        print('* Parsing texts...')

        docs = [doc for doc in nlp.pipe(texts, batch_size=1024, n_threads=8)]

        print('* Cleaning texts...')

        cleaned_texts = []
        for doc in docs:
            # Filter url and non alpha in text
            cleaned_text = ' '.join([token.text.lower() for token in doc if not self._unwanted_token(token,
                                                                                filter_stopwords=False,
                                                                                filter_url=True,
                                                                                filter_non_alpha=True)])
            cleaned_texts.append(cleaned_text)


        df['cleaned_text'] = cleaned_texts

        print('-'*116)

        return df

    def get_best_cluster_model(self, feature_vectors):
        # Choose a good cluster number by comparing silhouette score
        range_n_clusters = [3,4,5,6,7,8]

        best_cluster_model = None
        best_score = 0

        # For each number of clusters, perform Silhouette analysis.
        for n_clusters in range_n_clusters:

            # Cluster
            model = KMeans(n_clusters=n_clusters, verbose=False).fit(feature_vectors)

            # Compute the mean Silhouette Coefficient of all data points.
            s_mean = metrics.silhouette_score(feature_vectors, model.labels_)

            if best_score < s_mean:
                best_score = s_mean
                best_cluster_model = model

        return best_cluster_model, best_score

    def cluster(self, df):

        df = self.preprocess(df)

        try: cleaned_texts = df['cleaned_text']
        except: cleaned_texts = []

        print('* Transforming texts to feature vectors...')

        # Convert cleaned text to feature vectors
        feature_vectors = []
        for text in cleaned_texts:
            feature_vectors.append(np.array([[nlp.vocab[token].vector \
                                       for token in text.split()]]).sum(axis=1).ravel())

        feature_vectors = np.array(feature_vectors)

        print('* Clustering...')

        self.best_cluster_model, self.best_score = self.get_best_cluster_model(feature_vectors)

        print('* Done.')
        print('-'*116)

        del df['cleaned_text']
        df['cluster'] = self.best_cluster_model.labels_

        return df

if __name__ == '__main__':
    # Get data.
    data_helper = DataAggregator()
    date_range = [date.today().strftime('%Y-%m-%d')] # Only today.
    df = data_helper.get_data(date_range=date_range)

    # Cluster.
    df = Cluster().cluster(df)

    try: print(df.to_string())
    except: sys.stdout.buffer.write(df.to_string().encode('utf-8'))
