import os
import sys
import pickle
import pandas as pd

from tqdm import tqdm
from datetime import date, timedelta
from newspaper import Article

def get_url_content(url):
    try:
        print('Downloading "{}"'.format(url))
    except:
        print('Downloading url...')

    try:
        article = Article(url)
        article.download()
        article.parse()
        content = ' | '.join([article.title, article.text])
        return content.strip()
    except: return ''

dataset_folder_path = '../dataset/'

if __name__ == '__main__':

    sys.path.append('../data_helpers')
    from twitter_data_helper import TwitterDataHelper

    # Get data range
    start = date(2000, 1, 1)
    end = date.today()
    delta = end - start
    date_range = [(start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta.days + 1)]

    # Get data
    data_helper = TwitterDataHelper()
    df = data_helper.get_data(date_range=date_range)

    print('* {} rows retrieved.'.format(len(df)))
    print('* Prepare to download url content for each row...')

    # Extract URL
    df['url'] = df['raw_data'].apply(lambda raw_data: raw_data.entities \
                                                              .get('urls', [{}])[0] \
                                                              .get('expanded_url', ''))

    # For every URL, extract article
    data_file_path = os.path.join(dataset_folder_path, 'twitter_data_{}.pkl'.format(len(df)))

    df['url_content'] = [{} for _ in range(len(df))]

    for i, url in tqdm(enumerate(df['url'])):
        # Crawl url content
        df['url_content'][i] = get_url_content(url)

    print('* Saving...')
    df.to_pickle(data_file_path)
    print('* Done.')
