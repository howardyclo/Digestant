import os
import sys
import time
import json
import pickle
import pandas as pd

from tqdm import tqdm
from datetime import date

sys.path.append('../crawlers')
from url_content_crawler import get_url_content

class TwitterDataHelper(object):
    def __init__(self):
        self.config = self.get_config()

    def get_config(self):
        # Load config from json.
        try:
            with open('../config.json') as f:
                config = json.load(f)
                return config['twitter']
        except: return {}

    def to_dataframe(self, tweets, download_url_content=False):
        df = pd.DataFrame()
        df['source'] = ['twitter' for i in range(len(tweets))]
        df['created_at'] = [tweet.created_at.strftime('%Y-%m-%d %H:%M:%S') for tweet in tweets]
        df['author'] = [tweet.user.screen_name for tweet in tweets]
        df['text'] = [tweet.text for tweet in tweets]

        if download_url_content:
            # Extract url
            df['url'] = [tweet.entities.get('urls', [{}])[0].get('expanded_url', '') for tweet in tweets]

            # Download url content
            df['url_content'] = [{} for _ in range(len(df))]

            print('* [TwitterDataHelper] {} rows retrieved.'.format(len(df)))
            print('* [TwitterDataHelper] Prepare to download url content for each row...')

            for i, url in tqdm(enumerate(df['url'])):
                # Crawl url content
                df['url_content'][i] = get_url_content(url)

        df['raw_data'] = [tweet for tweet in tweets]

        return df

    def filter_tweets(self, tweets):
        def _unwanted(tweet):
            if tweet.lang not in ['en']:
                return True
            if tweet.in_reply_to_screen_name is not None:
                return True
            if 'RT' in tweet.text.split():
                return True
            if len(tweet.entities.get('urls', [])) == 0:
                return True

        return [tweet for tweet in tweets if not _unwanted(tweet)]

    def get_tweets(self, date_range=[]):

        dataset_folder_path = self.config['dataset_folder_path']

        if not os.path.exists(dataset_folder_path):
            print('! [TwitterDataHelper] You don\'t have a Twitter dataset folder.')
            print('! [TwitterDataHelper] You may want to get Twitter data by running `twitter_crawler.py` first.')
            return []

        if not date_range:
            date_range = [date.today().strftime('%Y-%m-%d')]

        # Get existed friends' screen names
        screen_names = os.listdir(dataset_folder_path)
        tweets = []
        for screen_name in screen_names:
            friend_folder_path = os.path.join(dataset_folder_path, screen_name)

            dates = [file_name.split('.')[0] for file_name in os.listdir(friend_folder_path)]

            tweets_file_paths =  [os.path.join(friend_folder_path, '{}.pkl'.format(date)) for date in dates if date in date_range]

            for tweets_file_path in tweets_file_paths:
                try:
                    with open(tweets_file_path, 'rb') as f:
                        tweets += pickle.load(f)
                except:
                    continue

        return self.filter_tweets(tweets)

    def get_data(self, date_range=[], download_url_content=False):
        if not date_range:
            date_range = [date.today().strftime('%Y-%m-%d')]
            
        tweets =  self.get_tweets(date_range=date_range)
        df = self.to_dataframe(tweets, download_url_content)
        return df

if __name__ == '__main__':
    data_helper = TwitterDataHelper()
    date_range = [date.today().strftime('%Y-%m-%d')] # Only today.
    df = data_helper.get_data(date_range=date_range)
    try: print(df.to_string())
    except: sys.stdout.buffer.write(df.to_string().encode('utf-8'))
