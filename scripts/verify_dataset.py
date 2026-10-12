"""Verify public data hashes, camera/image/mask correspondence and model headers.

Checks preservation and data contracts. It does not rerun reconstruction or
replace the historical topology/self-intersection checks with a new audit.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import struct


def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(4<<20),b""):
            h.update(block)
    return h.hexdigest()


def read_images_bin(path):
    images={}
    with path.open("rb") as f:
        count=struct.unpack("<Q",f.read(8))[0]
        for _ in range(count):
            record=struct.unpack("<i4d3di",f.read(64))
            name=bytearray()
            while True:
                char=f.read(1)
                assert char, "Truncated COLMAP image name"
                if char==b"\0":break
                name.extend(char)
            name=name.decode("utf-8")
            points=struct.unpack("<Q",f.read(8))[0]
            f.seek(points*24,1)
            assert name not in images
            images[name]={"image_id":record[0],"qvec":list(record[1:5]),
                          "tvec":list(record[5:8]),"camera_id":record[8]}
        assert f.read(1)==b"", "COLMAP images.bin trailing bytes"
    return images


def ply_header(path):
    result={}
    with path.open("rb") as f:
        assert f.readline()==b"ply\n"
        lines=[]
        while True:
            line=f.readline()
            assert line and len(lines)<100
            text=line.decode("ascii").strip();lines.append(text)
            if text.startswith("element "):
                _,name,count=text.split();result[name]=int(count)
            if text=="end_header":break
    assert all("property uchar "+x in lines for x in ["red","green","blue"])
    return result


def glb_header(path):
    with path.open("rb") as f:
        magic,version,length=struct.unpack("<4sII",f.read(12))
        assert magic==b"glTF" and version==2 and length==path.stat().st_size
        n,kind=struct.unpack("<II",f.read(8))
        assert kind==0x4E4F534A
        doc=json.loads(f.read(n))
    assert all("uri" not in b for b in doc["buffers"]), "External GLB buffer"
    vertex_count=face_count=0
    for mesh in doc["meshes"]:
        for primitive in mesh["primitives"]:
            a=primitive["attributes"]
            assert "POSITION" in a and "COLOR_0" in a and primitive.get("mode",4)==4
            n=doc["accessors"][a["POSITION"]]["count"]
            assert doc["accessors"][a["COLOR_0"]]["count"]==n
            indices=doc["accessors"][primitive["indices"]]["count"]
            assert indices%3==0
            vertex_count+=n;face_count+=indices//3
    return {"vertex":vertex_count,"face":face_count}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    ap.add_argument("--data-root",type=Path,help="Data directory, if outside the clone")
    ap.add_argument("--component",choices=["all","models","multiview"],default="all")
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    root=args.root.resolve();data=(args.data_root or root).resolve()
    collection=json.loads((root/"metadata/collection.json").read_text())
    inventory=json.loads((root/"metadata/files.json").read_text())["files"]
    rows=collection["objects"]
    assert [x["id"] for x in rows]==[f"DWK_{i:04d}" for i in range(1,42)]
    assert len({x["original_id"] for x in rows})==41
    selected=[x for x in inventory if args.component=="all" or x["component"]==args.component]
    for i,item in enumerate(selected,1):
        p=data/item["path"]
        assert p.resolve().is_relative_to(data) and p.is_file(), "Missing data: "+item["path"]
        assert p.stat().st_size==item["bytes"] and sha(p)==item["sha256"], "Data differs: "+item["path"]
        if i%2000==0:print("VERIFIED_HASHES",i,flush=True)
    actual={p.name for p in (data/"objects").iterdir() if p.is_dir()}
    assert actual=={x["id"] for x in rows}, "Missing or extra object directory"
    results=[]
    for row in rows:
        scene=data/"objects"/row["id"]
        result={"id":row["id"],"original_id":row["original_id"]}
        if args.component in {"all","models"}:
            assert ply_header(scene/"model.ply")=={"vertex":row["vertices"],"face":row["faces"]}
            assert glb_header(scene/"model.glb")=={"vertex":row["vertices"],"face":row["faces"]}
            assert json.loads((scene/"metadata.json").read_text())==row
            result["models"]="hashes, PLY/GLB counts and RGB attributes verified"
        if args.component in {"all","multiview"}:
            import numpy as np
            from PIL import Image
            cams=json.loads((scene/"cameras.json").read_text())
            registered={x["image"]:x for x in cams["registered_images"]}
            camera_dict={x["camera_id"]:x for x in cams["cameras"]}
            binary=read_images_bin(scene/"sparse/0/images.bin")
            views=list(csv.DictReader((scene/"views.csv").open(encoding="utf-8")))
            assert set(binary)==set(registered)=={Path(x["image"]).name for x in views}
            assert len(views)==row["image_count"]==row["mask_count"]
            assert {p.name for p in (scene/"images").iterdir()}==set(registered)
            assert {p.name for p in (scene/"masks").iterdir()}=={Path(x["mask"]).name for x in views}
            for view in views:
                name=Path(view["image"]).name;c=registered[name];b=binary[name]
                assert c["image_id"]==b["image_id"] and c["camera_id"]==b["camera_id"]==int(view["camera_id"])
                assert c["qvec_wxyz"]==b["qvec"] and c["tvec"]==b["tvec"]
                w2c=np.asarray(c["world_to_camera"],dtype=float)
                c2w=np.asarray(c["camera_to_world"],dtype=float)
                assert np.isfinite(w2c).all() and np.isfinite(c2w).all()
                assert np.allclose(w2c@c2w,np.eye(4),atol=1e-8,rtol=0)
                assert math.isclose(float(np.linalg.det(w2c[:3,:3])),1,abs_tol=1e-8)
                calibrated=camera_dict[c["camera_id"]]
                with Image.open(scene/view["image"]) as image, Image.open(scene/view["mask"]) as mask:
                    assert image.size==mask.size==(calibrated["width"],calibrated["height"])
                    assert mask.mode in {"L","1"}
            with (scene/"sparse/0/cameras.bin").open("rb") as f:
                assert struct.unpack("<Q",f.read(8))[0]==len(cams["cameras"])
            with (scene/"sparse/0/points3D.bin").open("rb") as f:
                assert struct.unpack("<Q",f.read(8))[0]==row["sparse_point_count"]
            result["multiview"]="hashes, COLMAP pose/name correspondence, inverse matrices, dimensions verified"
        results.append(result)
    report={"status":"passed","component":args.component,"objects":41,
            "files_verified":len(selected),"images":collection["image_count"] if args.component!="models" else None,
            "masks":collection["mask_count"] if args.component!="models" else None,
            "per_object":results,"new_topology_audit":False,
            "note":"Original model hashes preserve historical validation; this verifier does not measure hidden-surface accuracy"}
    if args.output:args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="per_object"},ensure_ascii=False))


if __name__=="__main__":main()
