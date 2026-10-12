"""Download selected public Release assets, check SHA256, and safely extract."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import stat
import urllib.request
import zipfile


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(4<<20),b""):h.update(b)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--component",choices=["all","models","multiview"],default="all")
    ap.add_argument("--output-root",type=Path)
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    dest=(args.output_root or root).resolve();dest.mkdir(parents=True,exist_ok=True)
    cache=dest/"downloads";cache.mkdir(exist_ok=True)
    release=json.loads((root/"metadata/releases.json").read_text())
    files=json.loads((root/"metadata/files.json").read_text())["files"]
    expected={x["path"]:x for x in files}
    for asset in release["assets"]:
        if args.component!="all" and asset["component"]!=args.component:continue
        archive=cache/asset["filename"]
        if not archive.is_file() or sha(archive)!=asset["sha256"]:
            temp=archive.with_suffix(archive.suffix+".part")
            print("DOWNLOAD",asset["url"],flush=True)
            request=urllib.request.Request(asset["url"],headers={"User-Agent":"Dawenkou-Digitization/1.0.0"})
            with urllib.request.urlopen(request,timeout=120) as response, temp.open("wb") as f:
                shutil.copyfileobj(response,f,4<<20)
            assert temp.stat().st_size==asset["bytes"] and sha(temp)==asset["sha256"], "Archive checksum differs"
            temp.replace(archive)
        with zipfile.ZipFile(archive) as z:
            selected={x["path"] for x in files if x["component"]==asset["component"]}
            assert len(z.namelist())==len(selected) and set(z.namelist())==selected
            for entry in z.infolist():
                path=dest/entry.filename
                assert not Path(entry.filename).is_absolute() and path.resolve().is_relative_to(dest)
                mode=entry.external_attr>>16
                assert not stat.S_ISLNK(mode), "Archive symlink is forbidden"
                if path.is_file():
                    assert sha(path)==expected[entry.filename]["sha256"], "Refusing to overwrite modified file: "+entry.filename
                    continue
                path.parent.mkdir(parents=True,exist_ok=True)
                with z.open(entry) as src,path.open("wb") as out:
                    shutil.copyfileobj(src,out,4<<20)
                assert sha(path)==expected[entry.filename]["sha256"]
        print("READY",asset["component"],asset["file_count"],"files",flush=True)
    print("Run scripts/verify_dataset.py for camera and model checks.")


if __name__=="__main__":main()
