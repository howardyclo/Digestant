import os
import sys
import time
import json
import pickle
import pandas as pd
import praw

from datetime import date

class RedditDataHelper(object):
    def __init__(self):
        self.config = self.get_config()
        self.reddit = praw.Reddit(client_id=self.config['client_id'],
                                  client_secret=self.config['client_secret'],
                                  password=self.config['password'],
                                  user_agent=self.config['user_agent'],
                                  username=self.config['username'])

    def get_config(self):
        # Load config from json.
        try:
            with open('../config.json') as f:
                config = json.load(f)
                return config['reddit']
        except: return {}

    def to_dataframe(self, submissions):
        df = pd.DataFrame()
        df['source'] = ['reddit' for i in range(len(submissions))]
        df['created_at'] = [date.fromtimestamp(submission.created).strftime('%Y-%m-%d') for submission in submissions]
        df['author'] = [submission.author.name for submission in submissions]
        df['text'] = [submission.title for submission in submissions]
        df['raw_data'] = [submission for submission in submissions]
        return df

    def get_submissions(self, channel='MachineLearning', querystring='deeplearning'):
        submission_generator = self.reddit.subreddit(channel).search(querystring)
        submissions = [submission for submission in submission_generator]
        return submissions

    def get_data(self, channel='MachineLearning', querystring='deeplearning'):

        submissions = self.get_submissions(channel='MachineLearning', querystring='deeplearning')
        df = self.to_dataframe(submissions)
        return df

if __name__ == '__main__':
    data_helper = RedditDataHelper()
    df = data_helper.get_data()
    try: print(df.to_string())
    except: sys.stdout.buffer.write(df.to_string().encode('utf-8'))
