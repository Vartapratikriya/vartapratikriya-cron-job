import os
import datetime

from pymongo import MongoClient
from dotenv import load_dotenv
from tqdm import tqdm

from news_listener import load_config, NewsListener
from keyword_extractor import KeywordExtractor
from sentiment_analyser import SentimentAnalyser


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
            domains={
                website: language
                for language, websites in self.config["outlets"].items()
                for website in websites
            },
            keywords=self.config["categories"],
        )
        self.extractor = KeywordExtractor()
        self.analyser = SentimentAnalyser()

    def generate_sentiment(self, data, type=None):
        print(f"Calculating sentiments for {type}...")

        if type == "headlines":
            for article in tqdm(data):
                article["sentiment"] = self.analyser(article["description"])["label"]
                article["sentiment_conf"] = self.analyser(article["description"])[
                    "score"
                ]

        elif type == "categorised":
            for article in tqdm(data):
                article["sentiment"] = self.analyser(article["description"])["label"]
                article["sentiment_conf"] = self.analyser(article["description"])[
                    "score"
                ]

        return data

    def generate_keywords(self, data, k=10):
        print("Getting top keywords...")
        keywords = []
        for article in tqdm(data):
            keywords.extend(self.extractor(article["title"]))

        word_counts = {}
        for string in keywords:
            word_counts[string] = word_counts.get(string, 0) + 1

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

        self.push_db(docs=top_dict, collection_name="top_keywords", type="one")
        self.push_db(docs=headlines_dict, collection_name="headlines", type="many")
        self.push_db(docs=categorised_dict, collection_name="categorised", type="many")

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
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HUGGINGFACE_HUB_ACCESS_TOKEN")
    job = CronJob()
    job.run()
