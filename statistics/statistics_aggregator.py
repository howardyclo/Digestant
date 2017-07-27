import os
import sys
import time
import json
import pickle
import pandas as pd

from datetime import date
from reddit_statistics import RedditStatistics
from twitter_statistics import TwitterStatistics

class StatisticsAggregator(object):
    def __init__(self, df):
        self.reddit_statistics = RedditStatistics(df)
        self.twitter_statistics = TwitterStatistics(df)

    def get_config(self):
        pass

    def get_stats(self, date_range=[]):
        twitter_df = self.twitter_statistics.get_stats()
        reddit_df = self.reddit_statistics.get_stats()
        df = pd.concat([twitter_df, reddit_df], axis=0, ignore_index=True)
        return df

if __name__ == '__main__':
    data_helper = DataAggregator()
    date_range = [date.today().strftime('%Y-%m-%d')] # Only today.
    df = data_helper.get_data(date_range=date_range)
    try: print(df.to_string())
    except: sys.stdout.buffer.write(df.to_string().encode('utf-8'))
