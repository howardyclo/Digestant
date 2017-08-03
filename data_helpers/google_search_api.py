import json
import requests
import pandas as pd

class GoogleCrawler(object):
    def __init__(self):
        self.config = self.get_config()
        self.key, self.cx = self.get_keys()

    def get_config(self):
        try:
            with open('../config.json') as f:
                config = json.load(f)
                return config['google']
        except: return {}

    def get_keys(self):
        key = self.config["api_key"]
        cx = self.config["search_id"]
        return key, cx

    def search(self, query):
        url = "https://www.googleapis.com/customsearch/v1"
        parameters = {"q": query,
                      "cx": self.cx,
                      "key": self.key,
                      }

        page = requests.request("GET", url, params=parameters)
        results = json.loads(page.text)
        df = self.process_search(results)
        return df

    def process_search(self, results):
        try:
            link_list = [item["link"] for item in results["items"]]
            df = pd.DataFrame(link_list, columns=["link"])
            df["title"] = [item["title"] for item in results["items"]]
            df["snippet"] = [item["snippet"] for item in results["items"]]
            return df
        except KeyError:
            print("API limit exceeded. You can only query 100 times per day")
            return {} 
            
