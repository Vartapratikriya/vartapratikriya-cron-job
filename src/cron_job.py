import os
import json
import datetime

from pymongo import MongoClient
from dotenv import load_dotenv
from tqdm import tqdm

from news_listener import NewsListener
from keyword_extractor import KeywordExtractor
from sentiment_analyser import SentimentAnalyser
from fact_checker import FactChecker


def load_config(config_file_path):
    try:
        with open(config_file_path, "r") as config_file:
            config = json.load(config_file)
        config["outlets"] = {
            website: language
            for language, websites in config["outlets"].items()
            for website in websites
        }
        return config
    except FileNotFoundError:
        print(f"Config file not found at {config_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in {config_file_path}: {e}")
        return None


class CronJob:
    def __init__(self) -> None:
        self.__version__ = "0.1.1"
        self.config = load_config("./config.json")
        self.cluster = MongoClient(
            f"mongodb+srv://007rajdeepghosh:{os.getenv('MONGODB_ATLAS_PASSWORD')}@api.rj03kl4.mongodb.net/?retryWrites=true&w=majority"
        )
        self.db = self.cluster["api"]
        self.listener = NewsListener(
            key=os.getenv("NEWS_API_KEY"),
            domains=self.config["outlets"],
            keywords=self.config["categories"],
        )
        self.extractor = KeywordExtractor()
        self.analyser = SentimentAnalyser()
        self.checker = FactChecker()

    def generate_fact(self, data, type=None):
        print(f"Calculating fact indices for {type}...")

        if type == "headlines":
            for article in tqdm(data):
                fact = self.checker(article["title"])
                article["fact"] = fact["label"]
                article["fact_conf"] = fact["score"]

        elif type == "categorised":
            for article in tqdm(data):
                fact = self.checker(article["description"])
                article["fact"] = fact["label"]
                article["fact_conf"] = fact["score"]

        return data

    def generate_sentiment(self, data, type=None):
        print(f"Calculating sentiment scores for {type}...")

        for article in tqdm(data):
            sentiment = self.analyser(article["description"])
            article["sentiment"] = sentiment["label"]
            article["sentiment_conf"] = sentiment["score"]

        return data

    def generate_keywords(self, data, k=10):
        print("Getting top keywords...")
        keywords = []
        for article in tqdm(data):
            keywords.extend(self.extractor(article["title"]))

        word_counts = {}
        for string in keywords:
            word_counts[string] = word_counts.get(string, 0) + 1

        if "" in word_counts.keys():
            del word_counts[""]

        most_common = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return {word: count for word, count in most_common[:k]}

    def push_db(self, docs, collection_name, type):
        print(f"Pushing {collection_name} to database...")
        collection = self.db[collection_name]
        collection.delete_many({})
        if type == "many":
            collection.insert_many(docs)
        elif type == "one":
            collection.insert_one(docs)

    def run(self) -> None:
        headlines = self.listener.get_headlines()
        categorised = self.listener.get_categorised()
        headlines_dict = self.generate_sentiment(data=headlines, type="headlines")
        categorised_dict = self.generate_sentiment(data=categorised, type="categorised")
        top_dict = self.generate_keywords(data=headlines_dict)
        factchecker_dict = self.generate_fact(data=categorised, type="headlines")

        self.push_db(docs=top_dict, collection_name="top_keywords", type="one")
        self.push_db(docs=headlines_dict, collection_name="headlines", type="many")
        self.push_db(docs=categorised_dict, collection_name="categorised", type="many")
        self.push_db(docs=factchecker_dict, collection_name="categorised", type="many")
        self.push_db(
            {
                "vartapratikriya-api": self.__version__,
                "status": "ok",
                "last_crawled": str(datetime.datetime.now()),
            },
            collection_name="status",
            type="one",
        )


if __name__ == "__main__":
    load_dotenv()
    job = CronJob()
    job.run()
