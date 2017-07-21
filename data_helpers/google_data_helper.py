import os
import sys
import time
import json
import pickle
import pandas as pd
import google_search

from datetime import date

class GoogleDataHelper(object):
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
        go = googlesearch.WebPage()
        query = go.prune(querystring)
        go.doquery(query)
        result = go.showpage(100)

        f1 = pd.DataFrame(result)
        f1.columns = ["text1","author","text2","text3"]
        f1["text"] = f1.ix[:,["text1","text2"]].apply(lambda x:x[0]+"|"+x[1],axis=1)
        f1["created_at"] = '2017-07-15'
        f1["source"] = "google"
        f1["raw_data"] = querystring
        f1.drop(["text1","text2",'text3'],axis=1,inplace=True)
        return f1

if __name__ == '__main__':
    data_helper = GoogleDataHelper()
    df = data_helper.get_data()
    try: print(df.to_string())
    except: sys.stdout.buffer.write(df.to_string().encode('utf-8'))
