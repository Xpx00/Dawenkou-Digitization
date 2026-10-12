"""Download the dataset and extract it into objects/."""
import argparse
import hashlib
from pathlib import Path
import urllib.request
import zipfile

BASE = "https://github.com/Xpx00/Dawenkou-Digitization-41/releases/download/v1.0.0/"
FILES = {'dawenkou41-models-v1.0.0.zip': 'e0a9ffbecfdf90ff0e3253042c4bf866e4afadf7cab95d5b3e0820570295541e', 'dawenkou41-multiview-v1.0.0.zip': '21d1540b2d6579e5f62b9a7ddd0e41e58fd8fd6c6ad17ae59c28c55f4e1a6f5a'}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    cache = root / "downloads"
    cache.mkdir(exist_ok=True)
    for name, expected in FILES.items():
        if args.models_only and "multiview" in name:
            continue
        archive = cache / name
        if not archive.exists() or digest(archive) != expected:
            print(f"Downloading {name}")
            temp = archive.with_suffix(".part")
            urllib.request.urlretrieve(BASE + name, temp)
            if digest(temp) != expected:
                raise RuntimeError(f"Incomplete download: {name}")
            temp.replace(archive)
        with zipfile.ZipFile(archive) as data:
            for name in data.namelist():
                if not (root / name).resolve().is_relative_to(root):
                    raise RuntimeError("Invalid archive path")
            data.extractall(root)
    print("Done.")


if __name__ == "__main__":
    main()
