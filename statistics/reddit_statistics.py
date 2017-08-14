import sys
import math
import operator
import re

import numpy as np
import pandas as pd
import json
sys.path.append('../data_helpers/')
from data_aggregator import DataAggregator

from datetime import date
from datetime import datetime, timedelta
from math import log
from operator import add
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime, timedelta

class RedditStatistics(object):
    def __init__(self, df):
        self.df = df
        self.submissions = self.get_submissions(df)

    def get_submissions(self, df):
        a = df[df['source'] == "reddit"].index.tolist()
        return [df["raw_data"][index] for index in a]

    def get_stats(self):
        df = pd.DataFrame()
        df = pd.DataFrame()
        df['source'] = ['reddit' for i in range(len(self.submissions))]
        df['created_at'] = [date.fromtimestamp(submission.created).strftime('%Y-%m-%d') for submission in self.submissions]
        df['author'] = [submission.author.name for submission in self.submissions]
        df['text'] = [submission.title for submission in self.submissions]
        a = self.df[self.df['source'] == "reddit"].index.tolist()
        df['url'] = [self.df["url"][index] for index in a]
        df["hotness"] = self.score()
        sentiment_score = self.sentiment_score()
        df["sentiment_polarity"] = sentiment_score
        df["sentiment"] = pd.Series(self.sentiment(sentiment_score), dtype="category")
        df['type'] = [self.what_type(url) for url in df['url']]
        return df

    def hot(self, ups, downs, date):
        epoch = datetime(1970, 1, 1)
        s = ups - downs
        order = log(max(abs(s), 1), 10)
        sign = 1 if s > 0 else -1 if s < 0 else 0

        td = date - epoch
        epoch_seconds = td.days * 86400 + td.seconds + (float(td.microseconds) / 1000000)
        seconds = epoch_seconds - 1134028003

        return round(sign * order + seconds / 45000, 7)

    def score(self):
        #get data for scoring
        upvotes = [submission.score for submission in self.submissions]
        downvotes = [submission.downs for submission in self.submissions]
        created = [datetime.fromtimestamp(submission.created) for submission in self.submissions]
        #score tweets
        score = [self.hot(s, d, c) for s, d, c in zip(upvotes, downvotes, created)]
        return score

    def sentiment_score(self):
        sid = SentimentIntensityAnalyzer()
        sentiment_score = [sid.polarity_scores(self.clean_url(submission.title)) for submission in self.submissions]

        return sentiment_score

    def sentiment(self, sentiment_score):
        sentiment = []
        for ss in sentiment_score:
            s = max(ss, key=ss.get)
            if s == "pos":
                sentiment.append("pos")
            elif s == " neg":
                sentiment.append("neg")
            else:
                sentiment.append("neu")

        return sentiment

    def clean_url(self, text):
        URLless_text = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text)
        return URLless_text
    
    def get_types(self):
        with open('../types.json') as f:
            return json.load(f)
        
    def get_domains(self):
        with open('../domains.json') as f:
            return json.load(f)
    
    def what_type(self, url):
        types = self.get_types()
        domains = self.get_domains()
        
        for key, value in types.items():
            for v in value:
                if v in url:
                    if key == 'reddit':
                        return 'subreddit: {}'.format(v)
                    if key == 'twitter':
                        return 'twitter status'
                else:
                    continue

        for d in domains:
            for urls in domains[d]:
                if urls in url:
                    return d
                else:
                    continue

        return "unknown link"

if __name__ == '__main__':
    data_helper = DataAggregator()
    date_range = [date.today().strftime('%Y-%m-%d')] # Only today.
    df = data_helper.get_data(date_range=date_range)

    reddit_stats = RedditStatistics(df)
    rdf = reddit_stats.get_stats()

    try: print(tdf.to_string())
    except: sys.stdout.buffer.write(df.to_string().encode('utf-8'))
