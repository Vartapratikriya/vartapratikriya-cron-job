import json
import requests
import datetime

from tqdm import tqdm
from typing import List, Dict


def load_config(config_file_path):
    try:
        with open(config_file_path, "r") as config_file:
            config = json.load(config_file)
        return config
    except FileNotFoundError:
        print(f"Config file not found at {config_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in {config_file_path}: {e}")
        return None


class NewsListener:
    def __init__(
        self,
        key: str,
        domains: Dict,
        keywords: List,
    ) -> None:
        self._key = key
        self.domains = domains
        self.keywords = keywords
        self.date = datetime.datetime.now().date().strftime("%y-%m-%d")
        self.url = (
            f"https://newsapi.org/v2/everything?from={self.date}&apiKey={self._key}"
        )

    def get_headlines(self) -> List:
        print("Getting headlines...")
        articles = []
        for domain in tqdm(self.domains.keys()):
            response = requests.get(self.url + f"&domains={domain}").json()["articles"]
            for article in response:
                article["language"] = self.domains[domain]
            articles.extend(response)
        return articles

    def get_categorised(self) -> List:
        print("Getting relevant articles...")
        articles = []
        for domain in tqdm(self.domains.keys()):
            for keyword in self.keywords:
                try:
                    response = requests.get(
                        self.url + f"&domains={domain}" + f"&q={keyword}"
                    ).json()["articles"]
                    for article in response:
                        article["category"] = keyword
                        article["language"] = self.domains[domain]
                        articles.append(article)
                except:
                    pass

        return articles
