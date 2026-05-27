import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from tqdm import tqdm

# Permet l'import depuis la racine du projet
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.config.config_loader import load_config

load_dotenv()
config = load_config()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
corpora = config["lexicon_corpora"]


headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    headers["Accept"] = "application/vnd.github+json"


def get_repo_info(github_url):
    parts = urlparse(github_url).path.strip("/").split("/")
    owner = parts[0]
    repo = parts[1]
    return owner, repo


def download_files(owner, repo, path="", save_dir=""):
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"

    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        print("Erreur API:", response.text)
        return

    items = response.json()

    for item in tqdm(items):
        if item["type"] == "dir":
            if item["name"] != "env":
                print(item["name"])
                download_files(owner, repo, item["path"], save_dir)

        elif item["type"] == "file":
            if item["name"].endswith((".xml", ".jpg")):
                file_url = item["download_url"]
                relative_path = item["path"]
                local_path = os.path.join(save_dir, relative_path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                file_data = requests.get(file_url, headers=headers).content
                with open(local_path, "wb") as f:
                    f.write(file_data)


def clone_repo(github_url):
    owner, repo = get_repo_info(github_url)
    save_dir = f"{corpora_dir}{repo}"

    if os.path.exists(save_dir):
        print(
            f"Folder {save_dir} already exists. Will not download. "
            "If this is an error please download it manually and add it to the correct directory."
        )
        return

    os.makedirs(save_dir)

    download_files(owner, repo, path="", save_dir=save_dir)


if __name__ == "__main__":
    for repository in tqdm(corpora, unit="corpus"):
        clone_repo(repository)
