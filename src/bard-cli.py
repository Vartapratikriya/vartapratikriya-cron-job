import os
import argparse

from dotenv import load_dotenv
from bardapi import Bard

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="bard-cli",
        description="Simple CLI to get prompt results from Google's BARD",
        epilog=":)",
    )
    parser.add_argument("--prompt")
    args = parser.parse_args()
    load_dotenv()
    token = os.getenv("BARD_ACCESS_TOKEN")

    bard = Bard(token=token)
    result = bard.get_answer(args.prompt)
    print(result["content"])
