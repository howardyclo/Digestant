from datetime import date
import sys
import re
import pandas as pd
sys.path.append('../data_helpers/')
from google_data_helper import GoogleDataHelper
from data_aggregator import DataAggregator
from time import sleep
import json
import wikipedia
import numpy as np

class DataOrganizer(object):
    def __init__(self, df):
        self.df = df
        self.data = self.get_data(df)
        self.domains = self.get_domains()
        self.results = self.google_search()
        self.hotness = self.get_hotness(df)

    def get_hotness(self, df):
        sys.path.append('../statistics/')
        from statistics_aggregator import StatisticsAggregator
        stats_helper = StatisticsAggregator(df)
        sdf = stats_helper.get_stats()
        return sdf['hotness']
        
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

    def google_search(self, num=10):
        results = []
        gd = GoogleDataHelper()
        print("* Google Searching Data...")
        for d, i in zip(self.data, range(len(self.data))):
            try:
                d = self.clean(d)
                print("* * Downloading ({}/{}) query".format(i+1, len(self.data)), end="\r")
                r = gd.get_data(querystring=d)
            except Exception as e:
                print("* * cannot download query ({}) because: ({})".format(i, str(e)))
                r = pd.DataFrame()
                continue

            results.append(r)
            sleep(5) #minimum time to not look like a bot/script

        print("* Download complete! ")
        return results

    def enhance(self, num=10):

        df = pd.DataFrame(columns=(list(self.domains.keys())))
        df["data"] = self.data
        df['source'] = self.df['source']
        df['results'] = self.results
        df['hotness'] = self.hotness

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
    
    def top(self, edf, num=3):
        a = edf.drop(list(set(edf.keys()) - set(self.domains.keys())), axis=1)
        
        hv_dict = {}
        for key, value in a.items():
            values = [v for v in value if len(v) != 0]
            hot_values = values[:3]
            hv_dict[key] = hot_values
     
        return hv_dict

    #def wiki_summarize(self):
        #import wikipedia
        #self.data

class SummarizeNER(object):
    def __init__(self, df):
        self.data = df
        self.cleaned_data = self.get_cleaned_data()
        self.cleaned_phrases = self.get_ner_tags()
        
    def get_cleaned_data(self):
        return [self.clean(text) for text in self.data['text']]


    def get_summarized_data(self):
        wikidf = pd.DataFrame(columns=("NER", "Summary"))
        wikidf["NER"] = self.cleaned_phrases
        wikidf["Summary"] = self.get_wiki_summary()
        return wikidf

    def del_repeat(self, seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    def get_wiki_summary(self, sentences=4):
        wiki_summary = []
        
        for phrase, i in zip(self.cleaned_phrases, range(len(self.cleaned_phrases))):
            print("Downloading ({}/{}) wikipedia page...".format(i+1, len(self.cleaned_phrases)), end="\r")
            try:
                summary = wikipedia.summary(phrase, sentences=sentences)
            except Exception as e:
                try:
                    a = str(e).splitlines()[1]
                    summary = wikipedia.summary(a, sentences=sentences)
                except:
                    summary = "No wikipedia page found"
                    pass
                pass
    
            wiki_summary.append(summary)
            
        return wiki_summary
    
    def clean(self, text, url=True, words_only=True, first_n_sent=(False, 4)):
        if url:
            text = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text)

        if words_only:
            regex = re.compile('[^a-zA-Z]')
            text = regex.sub(' ', text)

        if first_n_sent[0]:
            text = re.match(r'(?:[^.:;]+[.:;]){4}', text).group()

        return text

    def get_ner_tags(self):
        sys.path.append('../preprocess')
        from nltk.tag.stanford import StanfordNERTagger
        st = StanfordNERTagger('../stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz',
                      '../stanford-ner/stanford-ner.jar')        
        
        tokenized_list = [ct.split() for ct in self.cleaned_data]
        NERTags = st.tag_sents(tokenized_list)

        n = []
        for nt in NERTags:
            n.extend(nt)

        ids = []
        #get the indexes of all words that have NER tags
        ids = [i for a, i in zip(n, range(len(n))) if a[1] != "O"]
        a = np.array(ids)

        consecutive_ids = np.split(a, np.where(np.diff(a) != 1)[0]+1)

        phrases = []
        for ci in consecutive_ids:
            phrase = ""
            tag = ""
            for id_ in ci:
                phrase += "{} ".format(n[id_][0])

            tag += "{}".format(n[id_][1])
            phrases.append(phrase)

        cleaned_phrases = self.del_repeat(phrases)
        return cleaned_phrases

    if __name__ == '__main__':
        data_helper = DataAggregator()
        date_range = [date.today().strftime('%Y-%m-%d')] # Only today.
        df = data_helper.get_data(date_range=date_range)

        sn = SummarizeNER(df)
        sd = sn.get_summarized_data()
        print(sd.endode("UTF-8"))
