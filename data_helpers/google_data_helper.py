import os
import sys
import time
import json
import pickle
import pandas as pd

from datetime import date
from google_search import GoogleSearch

class GoogleDataHelper(object):
    def __init__(self):
        self.go = GoogleSearch()

    def get_data(self, querystring='deeplearning', num=10):
        query = self.go.prune(querystring)
        self.go.doquery(query, num)
        result = self.go.showpage(num)

        df = pd.DataFrame()

        created_at = date.today().strftime('%Y-%m-%d')
        df['source'] = ['google' for i in range(len(result))]
        df['created_at'] = [created_at for i in range(len(result))]
        df['author'] = [tup[1] for tup in result]
        df['text'] = ['|'.join([tup[0],tup[2]]) for tup in result]
        df['raw_data'] = [tup for tup in result]

        return df

if __name__ == '__main__':
    data_helper = GoogleDataHelper()
    df = data_helper.get_data()
    try: print(df.to_string())
    except: sys.stdout.buffer.write(df.to_string().encode('utf-8'))
