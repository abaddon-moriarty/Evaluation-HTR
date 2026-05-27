import os
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    headers["Accept"] = "application/vnd.github+json"


def get_repo_info(github_url):
    parts = urlparse(github_url).path.strip("/").split("/")
    owner = parts[0]
    repo = parts[1]
    return owner, repo


def download_files(owner, repo, path="", save_dir="downloaded_files"):
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        print("Erreur API:", response.text)
        return

    items = response.json()

    for item in items:
        if item["type"] == "dir":
            if item["name"] != "env":
                print(item["name"])
                download_files(owner, repo, item["path"], save_dir)

        elif item["type"] == "file":
            if item["name"].endswith((".xml")):
                file_url = item["download_url"]
                relative_path = item["path"]
                local_path = os.path.join(save_dir, relative_path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                file_data = requests.get(file_url, headers=headers).content
                with open(local_path, "wb") as f:
                    f.write(file_data)

owner, repo = get_repo_info("https://github.com/htR-United/cremma-medieval")
download_files(owner, repo, path="", save_dir=f"./data/corpora/{repo}")
