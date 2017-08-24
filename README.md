# Digestant
See [introduction slides](https://docs.google.com/presentation/d/18flIvwADXwQum-8xY6I3nSSQmWzqJCRrtQa9y23zVcM/edit?usp=sharing) and [project survey](https://hackmd.io/s/rkh_rJY4-)

## Dev Environment
- Python 3.x

## Setup
- NLTK data
  Download NLTK data: `$ python -m nltk.downloader all`.

- SpaCy model
  Download SpaCy **`en_core_web_md`** model: `$ python -m spacy download en_core_web_md`.

- Stanford NER model
  1. Download Stanford NER model from [the official website](https://nlp.stanford.edu/software/stanford-ner-2017-06-09.zip)
  2. Place the downloaded `stanford-ner-xxxx-xx-xx` folder the project root path. The name of folder should also be **`stanford-ner/`**

## Configuration
  1. First, copy `config-sample.json` and rename it to `config.json` in the same directory. Remember to fill the keys in `config.json`.
  2. Second, we need to crawl twitter data, so run the script `crawlers/twitter_crawler.py`. It will automatically crawl data and save them to `dataset/twitter/` by default.
