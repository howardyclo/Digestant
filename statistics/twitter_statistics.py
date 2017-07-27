import sys
import math
import operator
import re

import numpy as np
import pandas as pd

sys.path.append('../data_helpers/')
from data_aggregator import DataAggregator

from collections import Counter
from datetime import date
from datetime import datetime, timedelta
from math import log
from operator import add
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime, timedelta

class TwitterStatistics(object):
    def __init__(self, df):
        self.df = df
        self.tweets = self.get_tweets(df)
        
    def get_tweets(self, df):
        a = df[df['source'] == "twitter"].index.tolist()
        return [df["raw_data"][index] for index in a]
        
    def get_stats(self):
        df = pd.DataFrame()
        df['source'] = ['twitter' for i in range(len(self.tweets))]
        df['created_at'] = [tweet.created_at.strftime('%Y-%m-%d %H:%M:%S') for tweet in self.tweets]
        df['author'] = [tweet.user.screen_name for tweet in self.tweets]
        df['text'] = [tweet.text for tweet in self.tweets]
        df['hotness'] = self.score()
        sentiment_score = self.sentiment_score()
        df['sentiment_polarity'] = sentiment_score
        df["sentiment"] = pd.Series(self.sentiment(sentiment_score), dtype="category")
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
        retweet_count = [tweet.retweet_count for tweet in self.tweets]
        fav_count = [tweet.favorite_count for tweet in self.tweets]
        created_at = [tweet.created_at for tweet in self.tweets]
        #score tweets
        sums = [sum(x) for x in zip(fav_count, retweet_count)]
        score = [self.hot(s, 0, d) for s, d in zip(sums, created_at)]
        return score

    def sentiment_score(self):
        sid = SentimentIntensityAnalyzer()
        sentiment_score = [sid.polarity_scores(self.clean_url(tweet.text)) for tweet in self.tweets]

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
    
    def top_hashtags(self, X):
        h = []
        for tweet in self.tweets:
            a = [hashtags.get('text') for hashtags in tweet.entities.get('hashtags')]
            if len(a) > 0:
                h += a
            else:
                continue
                
        C = Counter(h)
        hashtags_l = [ [k,]*v for k,v in C.items()]
        a = sorted(hashtags_l,key = len, reverse=True)
        b = a[:X]
        return [t[0] for t in b]
    
    def top_mentions(self, X):
        h = []
        for tweet in self.tweets:
            user_name = tweet.user.screen_name
            usermentions = [usermentions.get('screen_name') for usermentions in tweet.entities.get("user_mentions")]
            if len(usermentions) > 0:
                h.extend(usermentions)
            else:
                continue

        c = Counter(h)
        return c.most_common(X)

if __name__ == '__main__':
    data_helper = DataAggregator()
    date_range = [date.today().strftime('%Y-%m-%d')] # Only today.
    df = data_helper.get_data(date_range=date_range)

    tweet_stats = TwitterStatistics(df)
    tdf = tweet_stats.get_data()

    try: print(tdf.to_string())
    except: sys.stdout.buffer.write(df.to_string().encode('utf-8'))
