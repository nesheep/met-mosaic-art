from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import requests

URL = "https://collectionapi.metmuseum.org/public/collection/v1"


def get_objects(query: str) -> tuple[int, list[int]]:
    params = {
        "hasImages": "true",
        "isPublicDomain": "true",
        "q": query,
    }
    data = requests.get(f"{URL}/search", params=params).json()
    return data["total"], data["objectIDs"]


def get_img_url(objectID: int) -> str | None:
    data = requests.get(f"{URL}/objects/{objectID}").json()
    if "primaryImage" in data:
        return data["primaryImage"]
    return None


def download_img(url: str, name: Path) -> None:
    data = requests.get(url).content
    name.write_bytes(data)


def main() -> None:
    try:
        save_path = Path(sys.argv[1])
        query = sys.argv[2]

        total, objectIDs = get_objects(query)
        print(f"total: {total}")

        save_path.mkdir(parents=True, exist_ok=True)
        print(f"mkdir: {save_path}\n")

        for i, objectID in enumerate(objectIDs):
            try:
                print(f"{datetime.now():%Y/%m/%d-%H:%M:%S} : {i + 1}/{total} {objectID} ...")
                img_url = get_img_url(objectID)
                if img_url:
                    print(f"img url: {img_url}")
                    name = save_path / f"{objectID}.jpg"
                    download_img(img_url, name)
                    print(f"save img: {name}")
                else:
                    print("no img")
            except Exception as e:
                print(f"error occurred: {objectID} {e}")
            finally:
                print()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
