from datetime import date
import sys
import re
import pandas as pd
sys.path.append('../data_helpers/')
from google_data_helper import GoogleDataHelper
from data_aggregator import DataAggregator
from time import sleep
import json

class GoogleDataEnhancer(object):
    def __init__(self, df):
        self.data = self.get_data(df)
        self.domains = self.get_domains()
        self.results = self.google_search()

    def get_data(self, df):
        a = df[df['source'] == "twitter"].index.tolist()
        tweet = [df["raw_data"][index].text for index in a]
        tweets = [self.clean(t) for t in tweet]
    
        a = df[df['source'] == "reddit"].index.tolist()
        subs = [df["raw_data"][index].title for index in a]
        
        data = tweets + subs
        return data
    
    def get_domains(self):
        with open("../domains.json", "r") as f:
            domains = json.load(f)
            
        return domains
        

    def clean(self, text):
        URLless_text = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text)
        regex = re.compile('[^a-zA-Z]')
        cleaned_text = regex.sub(' ', URLless_text)
        return cleaned_text

    def in_domain(self, url):
        
        for d in self.domains:
            for urls in self.domains[d]:
                if urls in url:
                    return d
                else:
                    continue
        return ""

    def google_search(self):
        results = []
        gd = GoogleDataHelper()
        print("* Google Searching Data...")
        for d, i in zip(self.data, range(len(self.data))):
            try:
                d = self.clean(d)
                print("* * Downloading ({}/{}) query".format(i+1, len(self.data)))
                r = gd.get_data(querystring=d)
            except Exception as e:
                print("* * cannot download query ({}) because: ({})".format(i, str(e)))
                r = pd.DataFrame()
                continue
            
            results.append(r)
            sleep(5) #minimum time to not look like a bot/script
        
        print("* Download complete! ")
        return results

    def enhance(self):

        df = pd.DataFrame(columns=(list(self.domains.keys())))
        df["data"] = self.data
        df['results'] = self.results

        for r, i in zip(self.results, range(len(self.results))):
            
            for d in self.domains:
                df[d][i] = []

            types = []
            type_dict = {}
            for url, text in zip(r['author'], r['text']):
                _type = self.in_domain(url)

                if _type != "":
                    t = (url, text)
                    df[_type][i].append(t)
             
                    
        return df
    
    #def wiki_summarize(self):
        #import wikipedia
        #self.data

    if __name__ == '__main__':
        data_helper = DataAggregator()
        date_range = [date.today().strftime('%Y-%m-%d')] # Only today.
        df = data_helper.get_data(date_range=date_range)

        gde = GoogleDataEnhancer(df)
        print(gde.enhance())
