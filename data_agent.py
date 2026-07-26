import pandas as pd
import re


def find_url(text):
    urls = re.findall(r'https?://\S+', text)
    return urls[0] if urls else None


def load_dataset(url):
    url = url.lower()

    if ".csv" in url:
        return pd.read_csv(url)

    elif ".xlsx" in url:
        return pd.read_excel(url)

    else:
        raise ValueError("Unsupported dataset format")