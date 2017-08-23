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
        self.encode_data(df)
        self.domains = self.get_domains()
        #self.results = self.google_search()
        self.hotness = self.get_hotness(df)

    def get_hotness(self, df):
        sys.path.append('../statistics/')
        from statistics_aggregator import StatisticsAggregator
        stats_helper = StatisticsAggregator(df)
        sdf = stats_helper.get_stats()
        return sdf['hotness']
        
    def encode_data(self, df):
        a = [t.encode('utf-8').strip() for t in df['text']]
        df['cleaned_text'] = a

    def get_domains(self):
        with open("../domains.json", "r") as f:
            domains = json.load(f)

        return domains

    def in_domain(self, url):

        for d in self.domains:
            for urls in self.domains[d]:
                if urls in url:
                    return d
                else:
                    continue
        return ""

    def enhance(self, num=10):
        from search_engine import SearchEngine
        se = SearchEngine()
        
        print("*[Data Organizer] Downloading Google Search Results")
        results = se.get_data(queries=self.df['cleaned_text'])
        
        results_t = []
        d = {}
        for r in results.items():
            tu = []
            for url, text in zip(r[1]['url'], r[1]['text']):
                tu.append((url, text))
            d = {'source_text': r[0], 'result': tu}
            results_t.append(d)
            
        
        self.df['google-search'] = [i for i in range(len(self.df))]
        for d, i in zip(self.df['cleaned_text'], range(len(self.df))):
            for r in results_t:
                if str(r['source_text']) == str(d):
                    self.df['google-search'][i] = r['result']
        
        q = []
        for gs in self.df['google-search']:
            types = dict((el, []) for el in list(self.domains))
            for result in gs:
                _type = self.in_domain(result[0])
                if _type != "": types[_type].append(result)
            q.append(types)
            
        self.df['types'] = q
        return self.df
    
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
        self.data['NER'] = self.cleaned_phrases
        self.data['Wiki-NER-Sumarry'] = self.get_wiki_summary()
        return self.data

    def del_repeat(self, seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    def get_wiki_summary(self, sentences=4):
        wiki_summary = []
        
        for phrase, i in zip(self.cleaned_phrases, range(len(self.cleaned_phrases))):
            if phrase != 'N/A':
                print("Downloading wikipedia pages...".format(i+1, len(self.cleaned_phrases)), end="\r")
                try:
                    summary = wikipedia.summary(phrase[0], sentences=sentences)
                except Exception as e:
                    try:
                        a = str(e).splitlines()[1]
                        summary = wikipedia.summary(a, sentences=sentences)
                    except:
                        summary = "No wikipedia page found"
                        pass
                    pass
            else:
                summary = "No wikipedia page found"
    
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
        
        tags = [nt for nt in NERTags]
        ids = [[i for a, i in zip(t, range(len(t))) if a[1] != "O"] for t in tags]
        
        phrases = []
        for i, t in zip(ids, tags):
            phrase = ""
            tt = "N/A"
            for p, index in zip(i, range(len(i))):
                if index == len(i) - 1:
                    phrase += "{}".format(t[p][0])
                    tt = phrase, t[p][1]
                else:
                    phrase += "{} ".format(t[p][0])

            phrases.append(tt)
        return phrases
        

    if __name__ == '__main__':
        data_helper = DataAggregator()
        date_range = [date.today().strftime('%Y-%m-%d')] # Only today.
        df = data_helper.get_data(date_range=date_range)

        sn = SummarizeNER(df)
        sd = sn.get_summarized_data()
        print(sd.endode("UTF-8"))
