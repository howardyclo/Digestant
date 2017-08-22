import os
import json
import pandas as pd
from datetime import date

""" Better than `google/bing_data_helper` since this module will not block users and it is much faster.

    Example usage:
    >> se = SearchEngine(verbose=True)
    >> search_results = se.search(search_engine='google', queries=['deep learning', 'reinforcement learning'])

    `search_engine` can be "google", "bing", "yahoo", "baidu" ... (See https://github.com/NikolaiT/GoogleScraper)
"""

class SearchEngine(object):

    def __init__(self, verbose=False,
                 search_engine='google',
                 queries_filepath='../dataset/cache/queries.txt',
                 output_filepath='../dataset/cache/output.json'):

        self.verbose = verbose
        self.search_engine = search_engine
        self.queries_filepath = queries_filepath
        self.output_filepath = output_filepath

    def _to_dataframe(self, result, keep_raw_data=False):

        df = pd.DataFrame()

        created_at = date.today().strftime('%Y-%m-%d')
        df['source'] = [self.search_engine for i in range(len(result['results']))]
        df['created_at'] = [created_at for i in range(len(result['results']))]
        df['author'] = [result['link'] for result in result['results']]
        df['text'] = [' | '.join([result['title'],result['snippet']]) for result in result['results']]
        df['url'] = [result['link'] for result in result['results']]

        return df

    def get_data(self, search_engine='', queries=[], to_dataframe=True):

        if search_engine != '':
            self.search_engine = search_engine

        if self.verbose: print('[*] Writing queries to "{}"...'.format(self.queries_filepath))
        with open(self.queries_filepath, 'w') as f:
            for word in queries:
                f.write('{}\n'.format(word))
            f.close()

        if self.verbose: print('[*] Searching queries and save results to "{}"...'.format(self.output_filepath))
        os.system('GoogleScraper -s "{}" --keyword-file {} --output-filename {} --num-workers=4'
              .format(self.search_engine, self.queries_filepath, self.output_filepath))

        if self.verbose: print('[*] Reading results from "{}"...'.format(self.output_filepath))
        with open(self.output_filepath) as f:
            self.results = json.load(f)
            f.close()

        if self.verbose: print('[*] Success.')

        if to_dataframe:
            return {result['query']: self._to_dataframe(result) for result in self.results}
        else:
            return self.results
