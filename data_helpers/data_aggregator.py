import os
import sys
import time
import json
import pickle
import pandas as pd

from datetime import date
from twitter_data_helper import TwitterDataHelper
from reddit_data_helper import RedditDataHelper
from google_data_helper import GoogleDataHelper

class DataAggregator(object):
    def __init__(self):
        self.twitter_data_helper = TwitterDataHelper()
        self.reddit_data_helper = RedditDataHelper()
        self.google_data_helper  = GoogleDataHelper()

    def get_config(self):
        pass

    def get_data(self, date_range=[]):
        twitter_df = self.twitter_data_helper.get_data(date_range=date_range)
        reddit_df = self.reddit_data_helper.get_data(date_range=date_range)
        google_df = self.google_data_helper.get_data()
        df = pd.concat([twitter_df, reddit_df, google_df], axis=0, ignore_index=True)
        return df

if __name__ == '__main__':
    data_helper = DataAggregator()
    date_range = [date.today().strftime('%Y-%m-%d')] # Only today.
    df = data_helper.get_data(date_range=date_range)
    try: print(df.to_string())
    except: sys.stdout.buffer.write(df.to_string().encode('utf-8'))
