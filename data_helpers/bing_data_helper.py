import os
import sys
import time
import json
import pickle
import pandas as pd

from datetime import date
from pws import Bing

class BingDataHelper(object):
    def __init__(self):
        pass

    def _get_config(self):
        pass

    def _to_dataframe(self, results, keep_raw_data=True):
        df = pd.DataFrame()

        created_at = date.today().strftime('%Y-%m-%d')
        df['source'] = ['bing' for i in range(len(results))]
        df['created_at'] = [created_at for i in range(len(results))]
        df['author'] = [result.get('link', '') for result in results]
        df['text'] = [' | '.join([result.get('link_text', ''), result.get('link_info', '')]) for result in results]
        df['url'] = [result.get('link', '') for result in results]

        if keep_raw_data:
            df['raw_data'] = [result for result in results]

        return df

    def get_data(self, querystring='deep learning', num=10, keep_raw_data=True):

        try:
            result = Bing.search(querystring, num=num, country_code='en')
        except:
            result = {}

        df = self._to_dataframe(result.get('results', []), keep_raw_data)

        return df

if __name__ == '__main__':
    data_helper = BingDataHelper()
    df = data_helper.get_data()
    try: print(df.to_string())
    except: sys.stdout.buffer.write(df.to_string().encode('utf-8'))
