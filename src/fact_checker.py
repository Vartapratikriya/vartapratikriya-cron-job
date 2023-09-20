from easygoogletranslate import EasyGoogleTranslate
from transformers import pipeline

from typing import Dict


class FactChecker:
    def __init__(self) -> None:
        self.clf = pipeline("text-classification", model="hamzab/roberta-fake-news-classification",
                            )
        self.translator = EasyGoogleTranslate()

    def __call__(self, string: str) -> Dict:
        return self.clf(self.translator.translate(text=string, target_language="en"))[0]
