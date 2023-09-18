from easygoogletranslate import EasyGoogleTranslate
from transformers import pipeline
from typing import *


class KeywordExtractor:
    def __init__(self) -> None:
        self.pipe = pipeline(
            "text2text-generation", model="Voicelab/vlt5-base-keywords"
        )
        self.translator = EasyGoogleTranslate()

    def __call__(self, string: str = None) -> List[str]:
        res = self.pipe(self.translator.translate(text=string, target_language="en"))[0]
        return [string.strip() for string in res["generated_text"].split(",")]
