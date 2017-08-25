# Digestant
See more on [introduction slides](https://docs.google.com/presentation/d/18flIvwADXwQum-8xY6I3nSSQmWzqJCRrtQa9y23zVcM/edit?usp=sharing), [project survey](https://hackmd.io/s/rkh_rJY4-) and [demo](https://github.com/YuChunLOL/Digestant/blob/master/demo/demo_howard.ipynb).

## Dev Environment
- Python 3.x

## Setup
- Recommended to create a new virtual environment to manage your python project.
- Download python packages from `requirements.txt`: `$ pip install -r requirements.txt`.
- Download NLTK data: `$ python -m nltk.downloader all`.
- Download SpaCy **`en_core_web_md`** model: `$ python -m spacy download en_core_web_md`.
- Download `stanford-ner-xxxx-xx-xx` zip file Stanford NER model
  1. Download from [the official website](https://nlp.stanford.edu/software/stanford-ner-2017-06-09.zip).
  2. Unzip and place the `stanford-ner-xxxx-xx-xx` folder the project root path. The name of folder should also be **`stanford-ner/`**.

## Usage
1. Create a twitter and reddit account, follow the accounts that you are interested in.
2. Copy `config-sample.json` and rename it to `config.json` in the same directory. Remember to fill the keys in `config.json`. (Go to your twitter/reddit developer console, create application and get keys.)
3. We need to crawl twitter data, so run the script `crawlers/twitter_crawler.py`. It will automatically crawl data and save them to `dataset/twitter/` by default.
4. You can customize data entities by modifying `domains.json` and `types.json`. (See [demo](https://github.com/YuChunLOL/Digestant/blob/master/demo/demo_howard.ipynb))
5. Currently, you can execute [`demo/demo_howard.ipynb`](https://github.com/YuChunLOL/Digestant/blob/master/demo/demo_howard.ipynb) or other notebooks to see daily digest.
