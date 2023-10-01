from easygoogletranslate import EasyGoogleTranslate
from transformers import pipeline

from typing import *


class SentimentAnalyser:
    def __init__(self) -> None:
        self.pipe = pipeline(
            "text-classification",
            model="mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis",
        )
        self.translator = EasyGoogleTranslate(timeout=25)

    def __call__(self, string: str) -> Dict:
        return self.pipe(self.translator.translate(text=string, target_language="en"))[
            0
        ]
