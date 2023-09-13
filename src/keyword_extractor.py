from typing import List
from langchain.llms import HuggingFaceHub


class KeywordExtractor:
    def __init__(self) -> None:
        pass

        self.llm = HuggingFaceHub(
            repo_id="Voicelab/vlt5-base-keywords", task="text2text-generation"
        )

    def __call__(self, string: str = None) -> List[str]:
        return [s.strip() for s in self.llm.predict(string).split(",")]
