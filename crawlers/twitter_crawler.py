import os
import sched, time
import pprint
import json
import pickle
import tweepy

from datetime import date, datetime
from threading import Timer
from datetime import timedelta

from collections import defaultdict

class TwitterCrawler(object):
    def __init__(self):
        # Setup
        self.config = self.get_config()
        self.api = self.get_api()
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def get_config(self):
        # Load config from json.
        try:
            with open('../config.json') as f:
                config = json.load(f)
                return config['twitter']
        except: return {}

    def get_api(self):
        """ Twitter API authentication and get API instance. """

        # Consumer keys and access tokens, used for OAuth
        consumer_key = self.config['consumer_key']
        consumer_secret = self.config['consumer_secret']
        access_token = self.config['access_token']
        access_token_secret = self.config['access_token_secret']

        # OAuth process, using the keys and tokens
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        # Creation of the actual interface, using authentication
        api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

        return api

    def get_friends(self):
        """ Get user's friend list in order to retrieve all of their tweets. """

        friends = []
        for friend in tweepy.Cursor(self.api.friends).items():
            friends.append(friend)

        return friends

    def get_friends_tweets(self, crawl_tweets_count=200):
        """
        Gets the newest tweets from a list of friends, then stores these tweets in a dictionary where
        the keys are named after the tweets date of creation. This dictionary is then stored in another dictionary,
        where the keys are named after the friend's screen name.
        """

        # Initialize friend list.
        if not hasattr(self, 'friends'):
            print('* Retrieving friend list...')
            self.friends = self.get_friends()
            print('* {} friends retrieved.'.format(len(self.friends)))

        friends_tweets = {friend.screen_name: defaultdict(lambda: []) for friend in self.friends}

        # For every friend, get their recent tweets
        for i, screen_name in enumerate(friends_tweets.keys()):

            print('* Progess: ({}/{})'.format(i+1, len(friends_tweets)))
            print('* Retrieving {}\'s tweets...'.format(screen_name))

            # Get tweets by screen name.
            try:
                tweets = self.api.user_timeline(screen_name=screen_name, count=crawl_tweets_count)
            # Handle error
            except Exception as e:
                print('! {}'.format(str(e)))
                continue

            # Segment tweets by date.
            print('* Segmenting {}\'s tweets by date...'.format(screen_name))
            tweets_keyed_by_date = self.segment_tweets_by_date(tweets)

            # Store date-segemented tweets to the corresponding friend.
            friends_tweets[screen_name] = tweets_keyed_by_date

            print('-'*116)

        return friends_tweets

    def save_friends_tweets(self, friends_tweets={}):
        """
        This function takes in the parameters of the `friends_tweets` dictionary.
        It saves the tweets under the directory: "{dataset_folder_path}/{screen_name}/{date}"
        """

        if not friends_tweets:
            print('* No tweets to save.')
            print('-'*116)
            return

        dataset_folder_path = self.config['dataset_folder_path']

        # Retrieve dictionary of tweets from individual friend
        for screen_name, tweets_keyed_by_date in friends_tweets.items():

            # Make folder for friends
            friend_folder_path = os.path.join(dataset_folder_path, screen_name)
            if not os.path.exists(friend_folder_path):
                print('* Making folder "{}" for a new friend: {}'.format(friend_folder_path, screen_name))
                os.makedirs(friend_folder_path)

            print('* Saving {}\'s tweets...'.format(screen_name))

            # Dumps tweets of same date in the same pickle file
            for date, tweets in tweets_keyed_by_date.items():
                # Save to pickle
                tweets_file_path = os.path.join(friend_folder_path, '{}.pkl'.format(date))
                with open(tweets_file_path, 'wb') as f:
                    # print('  - Writing to {} tweets to "{}"...'.format(len(tweet), tweets_file_path))
                    pickle.dump(tweets, f)

            print('* Save success.')
            print('-'*116)

    def restore_friends_tweets(self, only_latest=True, like_friends_tweets={}):
        """ Return a `friends_tweets` from file system.
            @param only_latest: if True, only restore latest tweets for every friend.
            @param like_friends_tweets: A dictionary same as `friends_tweets` structure,
                                        only restore tweets for friends (and dates) in `like_friends_tweets`.
        """

        dataset_folder_path = self.config['dataset_folder_path']

        if not os.path.exists(dataset_folder_path):
            print('* Making dataset folder "{}".'.format(dataset_folder_path))
            os.makedirs(dataset_folder_path)

        if not like_friends_tweets:
            friends_tweets = {screen_name: defaultdict(lambda: []) for screen_name in os.listdir(dataset_folder_path)}
        else:
            friends_tweets = {screen_name: defaultdict(lambda: []) for screen_name, _ in like_friends_tweets.items()}

        for screen_name in friends_tweets.keys():

            friend_folder_path = os.path.join(dataset_folder_path, screen_name)

            # Retrieve lastest tweets.
            if only_latest:
                file_names = self.get_latest_tweet_file_name(friend_folder_path)
                file_names = [] if file_names is None else [file_names] # For looping
            # Retrieve tweets only keyed by dates in `like_friends_tweets`.
            elif like_friends_tweets:
                file_names = ['{}.pkl'.format(date) for date in like_friends_tweets[screen_name].keys()]
            # Or retrieve all tweets.
            else:
                file_names = os.listdir(friend_folder_path)

            for file_name in file_names:
                # Read pickle, i.e. tweets_keyed_by_date
                tweets_file_path = os.path.join(friend_folder_path, file_name)

                try:
                    with open(tweets_file_path, 'rb') as f:
                        # print('* Reading tweets from "{}"...'.format(tweets_file_path))
                        tweets = pickle.load(f)
                except: tweets = []

                # Store tweets to dictionary
                date = file_name.split('.')[0]
                friends_tweets[screen_name][date] = tweets

        return friends_tweets

    def diff_friends_tweets(self, old_friends_tweets, new_friends_tweets):
        """ Compare the ids and return the difference (get newest tweets) """

        diff_friends_tweets = {screen_name: defaultdict(lambda: []) for screen_name, _ in new_friends_tweets.items()}

        for screen_name, tweets_keyed_by_date in new_friends_tweets.items():

            # Handle New friend, no need to diff.
            # Set `max_id` to 0, then all tweets from this new friend will be preserved.
            if screen_name not in old_friends_tweets.keys():
                max_id = 0
            else:
                old_tweets_keyed_by_date = old_friends_tweets[screen_name]
                old_tweets = self.tweets_keyed_by_date_tolist(old_tweets_keyed_by_date)
                try:
                    max_id = [tweet.id for tweet in old_tweets][0]
                except:
                    max_id = 0

            # Diff tweets by getting new tweets' ids that larger than the max id from `old_friends_tweets`.
            new_tweets = self.tweets_keyed_by_date_tolist(tweets_keyed_by_date)
            diff_tweets = [tweet for tweet in new_tweets if tweet.id > max_id]

            # Print info.
            if len(diff_tweets):
                print('* {} has new {} tweets'.format(screen_name, len(diff_tweets)))
                print('-'*116)

                # Segment tweets by date.
                diff_tweets_keyed_by_date = self.segment_tweets_by_date(diff_tweets)

                # Store date-segemented tweets to the corresponding friend.
                diff_friends_tweets[screen_name] = diff_tweets_keyed_by_date
            else:
                del diff_friends_tweets[screen_name]

        return diff_friends_tweets

    def merge_friends_tweets(self, diff_friends_tweets):
        """ Merge `diff_friends_tweets` with existed tweets in filesystem keyed by the same date. """

        old_friends_tweets = self.restore_friends_tweets(only_latest=False,
                                                         like_friends_tweets=diff_friends_tweets)

        merged_friends_tweets = diff_friends_tweets.copy()

        for screen_name, tweets_keyed_by_date in diff_friends_tweets.items():
            for date in tweets_keyed_by_date.keys():

                # Read old `tweets_keyed_by_date` from file system. (only specific dates that have new tweets)
                try: old_tweets = old_friends_tweets[screen_name][date]
                except: old_tweets = []

                # Append old tweets after new tweets.
                merged_friends_tweets[screen_name][date].extend(old_tweets)

        return merged_friends_tweets

    ############################################################################################
    ## Scheduled routines
    ############################################################################################

    def update_friends(self, repeat=False):
        """ Update `self.friends` if the user have new friends. """

        print('* Updating friends...')

        self.friends = self.get_friends()

        print('* {} friends updated.'.format(len(self.friends)))
        print('-'*116)

        # Repeat the same routine.
        if repeat:
            print('* Wait for next {} seconds to update friends...'.format(self.config['crawl_friends_freq']))
            self.scheduler.enter(delay=self.config['crawl_friends_freq'],
                                 priority=1,
                                 action=self.update_friends,
                                 argument=(True,))
        else:
            print('* Stop updating friends.')

    def update_friends_tweets(self, repeat=False):
        """ Get new tweets then appends them to old tweets and saves them to file system. """

        print('* Updating new tweets for {} friends...'.format(len(self.friends)))
        print('-'*116)

        # Restore current friends stored locally.
        old_friends_tweets = self.restore_friends_tweets(only_latest=True)

        # Get new tweets for each friend.
        new_friends_tweets = self.get_friends_tweets(crawl_tweets_count=self.config['crawl_tweets_count'])

        # Compare the ids and return the difference (get new tweets that are not existed in old tweets)
        diff_friends_tweets = self.diff_friends_tweets(old_friends_tweets, new_friends_tweets)

        # Merge diff tweets with existed tweets in filesystem keyed by the same date.
        merge_friends_tweets = self.merge_friends_tweets(diff_friends_tweets)

        # Save merged tweets into file system.
        self.save_friends_tweets(merge_friends_tweets)

        # Repeat the same routine.
        if repeat:
            print('* Wait for next {} seconds to update new tweets...'.format(self.config['crawl_tweets_freq']))
            self.scheduler.enter(delay=self.config['crawl_tweets_freq'],
                                 priority=1,
                                 action=self.update_friends_tweets,
                                 argument=(True,))
        else:
            print('* Stop updating friends.')

    ############################################################################################
    ## Utility functions
    ############################################################################################

    def get_latest_tweet_file_name(self, friend_folder_path):
        """ Get latest tweet file name from a specific path in file system. """

        date_strs = (file_name.split('.')[0] for file_name in os.listdir(friend_folder_path))
        dates = []

        for date_str in date_strs:
            dates.append(date(*[int(x) for x in date_str.split('-')]))

        if len(dates):
            latest_date = max(dates)
            latest_date_str = latest_date.strftime('%Y-%m-%d')
            latest_file_name = '{}.pkl'.format(latest_date_str)
            return latest_file_name
        else:
            return None

    def segment_tweets_by_date(self, tweets):
        """ Convert tweet list to `tweets_keyed_by_date` dictionary:
            - key: date string (e.g. '2017-01-01')
            - value: tweet list.
        """
        tweets_keyed_by_date = defaultdict(lambda: [])

        for tweet in tweets:
            date = tweet.created_at.strftime('%Y-%m-%d')
            tweets_keyed_by_date[date].append(tweet)

        return tweets_keyed_by_date

    def tweets_keyed_by_date_tolist(self, tweets_keyed_by_date):
        """
        Convert `tweets_keyed_by_date` dictionary to tweet list.
        Reverse function of `segment_tweets_by_date()`.
        """

        tweets = []
        sorted_dates = sorted(tweets_keyed_by_date.keys(), reverse=True)
        # Flatten tweets ordered by date in descent order
        for date in sorted_dates:
            tweets.extend([tweet for tweet in tweets_keyed_by_date[date]])
        return tweets

    ############################################################################################
    ## Main routine
    ############################################################################################

    def start(self, require_initial_tweets='n'):
        """ Main routine """

        # Initialize friend list.
        if not hasattr(self, 'friends'):
            self.update_friends(repeat=False)

        if require_initial_tweets == 'y':
            print('* Retrieving initial {} tweets for all of {} friends from Twitter...'.format(self.config['initial_crawl_tweets_count'],
                                                                                                len(self.friends)))
            friends_tweets = self.get_friends_tweets(crawl_tweets_count=self.config['initial_crawl_tweets_count'])
            self.save_friends_tweets(friends_tweets)

        else:
            # Initial update friend tweets
            self.update_friends_tweets(repeat=False)

        # Schedule routines (update friend list and new tweets)
        print('* Wait for next {} seconds to update friends...'.format(self.config['crawl_friends_freq']))
        self.scheduler.enter(delay=self.config['crawl_friends_freq'],
                             priority=1,
                             action=self.update_friends,
                             argument=(True,))

        print('* Wait for next {} seconds to update new tweets...'.format(self.config['crawl_tweets_freq']))
        self.scheduler.enter(delay=self.config['crawl_tweets_freq'],
                             priority=1,
                             action=self.update_friends_tweets,
                             argument=(True,))

        # Run all scheduled events
        self.scheduler.run()

def main():
    # Initialize crawler
    crawler = TwitterCrawler()

    # Handle crawler options
    require_initial_tweets = 'n'
    if not os.path.exists(crawler.config['dataset_folder_path']):
        print('* You don\'t have any tweets now.')
        print('* Do you want to crawl initial tweets from every friend?')
        print('  - If yes, the crawler will initially crawl {} most-recent tweets from every friend.'.format(crawler.config['initial_crawl_tweets_count']))
        print('  - If no, the crawler will crawl {} most-recent tweets and only save new tweets in every {} minutes.'.format(crawler.config['crawl_tweets_count'],
                                                                                                                             crawler.config['crawl_tweets_freq']))
        valid_input = False
        while not valid_input:
            require_initial_tweets = input('* Please input (y/n)')
            if require_initial_tweets.lower() in ['y', 'n']: valid_input = True

    # Start crawling
    crawler.start(require_initial_tweets)

if __name__ == '__main__':
    main()
