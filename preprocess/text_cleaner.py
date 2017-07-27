import spacy
print('* [TextCleaner] Loading SpaCy "en_core_web_md" corpus...')
nlp = spacy.load('en_core_web_md')
print('* [TextCleaner] Success.')
print('-'*116)

from tqdm import tqdm
from nltk.corpus import stopwords

class TextCleaner(object):
    def __init__(self, language_whitelist=['en'], token_blacklist=['rt'],
                 filter_stopwords=True, filter_sentiment_words=False, filter_url=True,
                 filter_digit=True, filter_number=True, filter_pronoun=True,
                 filter_non_alpha=True, filter_non_ascii=True, filter_character=True):

        self.language_whitelist = ['en']
        self.token_blacklist = ['rt']
        self.filter_stopwords = filter_stopwords
        self.filter_sentiment_words = filter_sentiment_words
        self.filter_url = filter_url
        self.filter_digit = filter_digit
        self.filter_number = filter_number
        self.filter_pronoun = filter_pronoun
        self.filter_non_alpha = filter_non_alpha
        self.filter_non_ascii = filter_non_ascii
        self.filter_character = filter_character

        # Load NLTK stopwords
        if filter_stopwords:
            self._load_stopwords()

        # Load sentinent words
        if filter_sentiment_words:
            self._load_sentiment_words()

    def _load_stopwords(self):
        print('* [TextCleaner] Loading stopwords...')
        try:
            self.stopwords = stopwords.words('english')
        except:
            print('! [TextCleaner] Failed to load stopwords.')
            self.stopwords = []

    def _load_sentiment_words(self):
        print('* [TextCleaner] Loading sentinent words...')
        try:
            with open('../corpus/pos_words.txt') as f:
                self.pos_words = [line.replace('\n', '') for line in f.readlines()]
        except:
            print('! [TextCleaner] Failed to load positive words.')
            self.pos_words = []

        try:
            with open('../corpus/neg_words.txt') as f:
                self.neg_words = [line.replace('\n', '') for line in f.readlines()]
        except:
            print('! [TextCleaner] Failed to load negative words.')
            self.neg_words = []

        self.sentiment_words = self.pos_words + self.neg_words

    def _unwanted_token(self, token):

        if self.language_whitelist and token.lang_ not in self.language_whitelist:
            return True
        if self.token_blacklist and token.text.lower() in self.token_blacklist:
            return True
        if self.filter_stopwords and (token.is_stop or token.text.lower() in self.stopwords):
            return True
        if self.filter_url and token.like_url:
            return True
        if self.filter_digit and token.is_digit:
            return True
        if self.filter_number and token.like_num:
            return True
        if self.filter_pronoun and token.lemma_ == '-PRON-':
            return True
        if self.filter_non_alpha and not token.is_alpha:
            return True
        if self.filter_non_ascii and not token.is_ascii:
            return True
        if self.filter_character and not len(token.text) > 1:
            return True
        if self.filter_sentiment_words and token.text.lower() in self.sentiment_words:
            return True

        return False

    def clean(self, texts=[]):
        print('* [TextCleaner] Cleaning text ...')
        docs = [doc for doc in tqdm(nlp.pipe(texts, batch_size=1024, n_threads=8))]
        return [[token.lemma_.lower() for token in doc if not self._unwanted_token(token)] for doc in docs]
