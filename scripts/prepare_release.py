"""Build a minimal, consecutively numbered release without editing its source.

The prepared objects are distributed as GitHub Release assets, not Git blobs.
All retained image/mask/model/COLMAP bytes must match the source checksums.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def dump(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")


def write_csv(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--audit-dir", type=Path, required=True,
                    help="Internal build audit outside the public repository")
    args = ap.parse_args()
    source, root = args.source.resolve(), args.root.resolve()
    assert source != root and not (root/"objects").exists()
    assert not args.audit_dir.resolve().is_relative_to(root)
    manifest = json.loads((source/"MANIFEST.json").read_text())
    previous_validation = json.loads((source/"VALIDATION_REPORT.json").read_text())
    old_objects = sorted(manifest["objects"], key=lambda x: int(x["id"].split("_")[1]))
    assert len(old_objects) == len({x["id"] for x in old_objects}) == 41
    assert previous_validation["status"] == "passed"
    validated = {x["id"]: x for x in previous_validation["per_object"]}
    expected = {}
    for line in (source/"SHA256SUMS.txt").read_text().splitlines():
        digest, rel = line.split("  ", 1)
        assert rel not in expected and (source/rel).resolve().is_relative_to(source)
        expected[rel] = digest
    # Source extras are classified below, but never treated as authoritative.
    for n, (rel, digest) in enumerate(expected.items(), 1):
        assert (source/rel).is_file(), "Source file missing: "+rel
        assert sha(source/rel) == digest, "Source checksum mismatch: "+rel
        if n % 2000 == 0:
            print("SOURCE_HASHES", n, flush=True)
    actual = {p.relative_to(source).as_posix(): p.stat().st_size
              for p in source.rglob("*") if p.is_file()}
    extras = sorted(set(actual)-set(expected)-{"SHA256SUMS.txt"})
    assert all(Path(x).name == ".DS_Store" or x == "multiview/DWK_0073.zip"
               for x in extras), "Unexpected source extras require inspection"
    (root/"objects").mkdir()
    kept, mappings, objects, compact_validation = [], [], [], []
    duplicate_masks = redundant_sparse_ply = 0
    original_frame_bytes = 0

    def copy_checked(src, dest):
        rel = src.relative_to(source).as_posix()
        assert rel in expected
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        digest = sha(dest)
        assert digest == expected[rel]
        kept.append({"source_relative_path": rel,
                     "published_relative_path": dest.relative_to(root).as_posix(),
                     "sha256": digest, "bytes": dest.stat().st_size})
        return digest

    for index, original in enumerate(old_objects, 1):
        old, new = original["id"], f"DWK_{index:04d}"
        row_validation = validated[old]
        assert original["acceptance_status"] == "manual_accepted"
        assert row_validation["watertight"] and row_validation["edge_manifold"]
        assert row_validation["components"] == 1 and row_validation["glb_rgb_and_indices_roundtrip"]
        assert row_validation["mesh_ply_sha256"] == original["mesh_ply_sha256"]
        dest = root/"objects"/new
        dest.mkdir()
        ply_sha = copy_checked(source/original["mesh_ply"], dest/"model.ply")
        glb_sha = copy_checked(source/original["mesh_glb"], dest/"model.glb")
        assert ply_sha == original["mesh_ply_sha256"] and glb_sha == original["mesh_glb_sha256"]
        mv = source/original["multiview_directory"]
        views = list(csv.DictReader((mv/"VIEW_INDEX.csv").open(encoding="utf-8-sig")))
        cams = json.loads((mv/"cameras.json").read_text())
        registered = {x["image"] for x in cams["registered_images"]}
        assert len(views) == original["image_count"] == original["registered_view_count"]
        assert len(registered) == len(views)
        image_names, mask_names = set(), set()
        view_output = []
        for view in views:
            image = Path(view["image"])
            mask = Path(view["mask"])
            assert image.parts[0] == "images" and mask.parts[0] == "masks"
            assert len(image.parts) == len(mask.parts) == 2
            assert image.name in registered and view["registered"].lower() == "true"
            assert image.name not in image_names and mask.name not in mask_names
            image_names.add(image.name); mask_names.add(mask.name)
            copy_checked(mv/image, dest/image)
            copy_checked(mv/mask, dest/mask)
            original_frame_bytes += (mv/image).stat().st_size
            # The published mask is the exact file indexed by the original view table.
            duplicate = (mv/mask).with_name(Path(image.name).stem+".png")
            assert duplicate != mv/mask and duplicate.is_file()
            assert expected[duplicate.relative_to(source).as_posix()] == expected[(mv/mask).relative_to(source).as_posix()]
            duplicate_masks += 1
            view_output.append({"image": image.as_posix(), "mask": mask.as_posix(),
                                "registered": True, "camera_id": int(view["camera_id"])})
        assert {p.name for p in (mv/"images").iterdir() if p.is_file()} == image_names
        assert len([p for p in (mv/"masks").iterdir() if p.suffix==".png"]) == 2*len(views)
        for name in ["cameras.bin", "images.bin", "points3D.bin", "rigs.bin", "frames.bin"]:
            copy_checked(mv/"sparse/0"/name, dest/"sparse/0"/name)
        assert (mv/"sparse/0/points3D.ply").is_file()
        redundant_sparse_ply += 1
        copy_checked(mv/"cameras.json", dest/"cameras.json")
        write_csv(dest/"views.csv", view_output)
        item = {"id": new, "original_id": old, "name_zh": original["name"],
                "description_zh": original["description"], "category": original["category"],
                "completion_method": original["completion_method"],
                "support_route": original["support_route"],
                "acceptance_status": "manual_accepted", "review_date": original["review_date"],
                "up_axis": original["up_axis"], "front_axis": original["front_axis"],
                "coordinate_frame": original["coordinate_frame"], "units": original["units"],
                "model_ply": f"objects/{new}/model.ply", "model_glb": f"objects/{new}/model.glb",
                "model_ply_sha256": ply_sha, "model_glb_sha256": glb_sha,
                "image_count": len(views), "registered_view_count": len(registered),
                "mask_count": len(views), "sparse_point_count": row_validation["multiview"]["point_count"],
                "vertices": original["vertices"], "faces": original["faces"],
                "color_source": original["color_source"],
                "hidden_surface_note": original["hidden_bottom_geometry_and_color"]}
        dump(dest/"metadata.json", item)
        objects.append(item)
        mappings.append({"id": new, "original_id": old, "name_zh": original["name"],
                         "category": original["category"]})
        compact_validation.append({"id":new,"original_id":old,
            "model_ply_sha256":ply_sha,"model_glb_sha256":glb_sha,
            "source_validation_preserved_by_byte_identical_models":True,
            "source_recorded_watertight":True,"source_recorded_edge_manifold":True,
            "source_recorded_components":1,"source_recorded_glb_roundtrip":True,
            "source_reprojection_mean_px":row_validation["multiview"]["reprojection_mean_px"],
            "source_reprojection_p95_px":row_validation["multiview"]["reprojection_p95_px"]})
        print("PREPARED", new, "FROM", old, "views", len(views), flush=True)

    image_count = sum(x["image_count"] for x in objects)
    assert image_count == manifest["image_count"] == 4620
    assert duplicate_masks == 4620 and redundant_sparse_ply == 41
    collection = {"schema":"dawenkou_digitization_release_v1", "title":"Dawenkou Digitization: Curated Watertight 41",
                  "version":"1.0.0", "source_package_version":manifest["version"],
                  "publisher_github_login":"Xpx00", "repository":"https://github.com/Xpx00/Dawenkou-Digitization",
                  "license":"CC-BY-NC-4.0", "license_url":"https://creativecommons.org/licenses/by-nc/4.0/",
                  "object_count":41,"category_counts":manifest["category_counts"],
                  "image_count":image_count,"registered_view_count":image_count,"mask_count":image_count,
                  "completion_branch_counts":{"HVE":sum(o["completion_method"]=="HVE" for o in objects),
                                              "T0":sum(o["completion_method"]=="T0" for o in objects)},
                  "id_policy":"Consecutive numbering 0001..0041, sorted by original numeric ID; map retained",
                  "split_policy":"No independent train/validation/test split; curated application outputs",
                  "geometric_ground_truth":False,"metric_scale_calibrated":False,
                  "hidden_surfaces":"Completion/extrapolation, not independently measured ground truth",
                  "source_manifest_sha256":sha(source/"MANIFEST.json"),
                  "source_validation_sha256":sha(source/"VALIDATION_REPORT.json"),
                  "model_and_input_bytes_unchanged":True,"objects":objects}
    assert collection["completion_branch_counts"] == {"HVE":33,"T0":8}
    dump(root/"metadata/collection.json", collection)
    write_csv(root/"metadata/id_mapping.csv", mappings)
    columns=["id","original_id","name_zh","category","completion_method","image_count",
             "registered_view_count","mask_count","sparse_point_count","vertices","faces",
             "model_ply","model_glb","model_ply_sha256","model_glb_sha256"]
    write_csv(root/"metadata/objects.csv",[{k:o[k] for k in columns} for o in objects])
    dump(root/"metadata/model_validation.json", {
        "scope":"Historical accepted-model checks, bound to unchanged model hashes; no new self-intersection audit",
        "source_validation_sha256":collection["source_validation_sha256"],"objects":compact_validation})
    data_files=[]
    for path in sorted((root/"objects").rglob("*")):
        if path.is_file():
            data_files.append({"path":path.relative_to(root).as_posix(),"bytes":path.stat().st_size,
                               "sha256":sha(path),
                               "component":"models" if path.name in {"model.ply","model.glb","metadata.json"} else "multiview"})
    dump(root/"metadata/files.json",{"files":data_files,"file_count":len(data_files)})
    (root/"metadata/SHA256SUMS.txt").write_text("".join(x["sha256"]+"  "+x["path"]+"\n" for x in data_files))
    dump(root/"metadata/completion_recipe.json", {
        "recipe_source":"Frozen parameters associated with the original accepted subset",
        "gaussian_training_iterations":15000,"surface_extraction":"2DGS TSDF",
        "completion_solver":"Screened Poisson", "poisson":manifest["recipe"],
        "HVE_envelope":{"grid_size":128,"construction_views":32,"mask_max_dimension":512,
                        "guard_pixels":2,"outside_consensus":2,"dilation_in_source_height":0.06},
        "branches":{"HVE":"foreground-envelope-constrained Poisson","T0":"standard Poisson"},
        "all_models_from_envelope_branch":False,
        "note":"Historical selected outputs; prior caches, Gaussian checkpoints and source TSDF are not bundled"})
    # Archive only data; the Git checkout supplies metadata and verification scripts.
    assets=root/"release_assets";assets.mkdir()
    archive_records=[]
    for component in ["models","multiview"]:
        name=f"dawenkou41-{component}-v1.0.0.zip"
        archive=assets/name
        selected=[x for x in data_files if x["component"]==component]
        with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for item in selected:
                z.write(root/item["path"],item["path"])
        with zipfile.ZipFile(archive) as z:
            assert set(z.namelist())=={x["path"] for x in selected}
            assert z.testzip() is None
        archive_records.append({"component":component,"filename":name,"bytes":archive.stat().st_size,
                                "sha256":sha(archive),"file_count":len(selected),
                                "url":"https://github.com/Xpx00/Dawenkou-Digitization/releases/download/v1.0.0/"+name})
        print("ARCHIVE_VERIFIED",name,archive.stat().st_size,flush=True)
    dump(root/"metadata/releases.json",{"tag":"v1.0.0","assets":archive_records})
    (assets/"SHA256SUMS.txt").write_text("".join(x["sha256"]+"  "+x["filename"]+"\n" for x in archive_records))
    audit={"status":"prepared_and_hash_verified","source":str(source),"new_repository":str(root),
           "source_checksum_files_verified":len(expected),"source_extras_not_published":extras,
           "source_metadata_sha256":collection["source_manifest_sha256"],
           "copied_byte_identical_files":len(kept),"removed_duplicate_masks":duplicate_masks,
           "removed_generated_sparse_ply":redundant_sparse_ply,"kept_files":kept,
           "object_count":41,"image_count":image_count,"mask_count":image_count,
           "original_source_unchanged":True,"source_bytes":sum(actual.values()),
           "data_bytes":sum(x["bytes"] for x in data_files),"archives":archive_records}
    dump(args.audit_dir/"BUILD_AUDIT.json",audit)
    print("PUBLIC_RELEASE_PREPARED",len(data_files),"files",audit["data_bytes"],"bytes",flush=True)


if __name__ == "__main__":
    main()
