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

        created_at = []
        author = []
        text = []
        raw_data = []

        for submission in submissions:
            created_at.append(date.fromtimestamp(submission.created).strftime('%Y-%m-%d'))
            author.append('{}|{}'.format(submission.subreddit, submission.author.name))
            text.append(submission.title)
            raw_data.append(submission)

        df = pd.DataFrame()
        df['source'] = ['reddit' for i in range(len(submissions))]
        df['created_at'] = created_at
        df['author'] = author
        df['text'] = text
        df['raw_data'] = raw_data

        return df

    def get_submissions(self, date_range=[]):
        if not date_range:
            date_range = [date.today().strftime('%Y-%m-%d')]

        channels = '+'.join(self.config['channels'])

        submissions = [submission for submission in self.reddit.subreddit(channels).new()
                        if date.fromtimestamp(submission.created).strftime('%Y-%m-%d') in date_range]

        return submissions

    def get_data(self, date_range=[]):
        if not date_range:
            date_range = [date.today().strftime('%Y-%m-%d')]

        submissions = self.get_submissions(date_range)
        df = self.to_dataframe(submissions)
        return df

if __name__ == '__main__':
    data_helper = RedditDataHelper()
    df = data_helper.get_data()
    try: print(df.to_string())
    except: sys.stdout.buffer.write(df.to_string().encode('utf-8'))
