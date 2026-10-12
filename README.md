# Dawenkou Digitization · Curated Watertight 41

[中文说明](README.zh-CN.md) · [Download data](https://github.com/Xpx00/Dawenkou-Digitization/releases/tag/v1.0.0) · [Object index](metadata/objects.csv) · [ID mapping](metadata/id_mapping.csv)

A curated collection of **41 manually reviewed colored watertight models**
and their reconstruction inputs from Dawenkou artifact videos. The collection
contains **40 ceramic artifacts and one stone spindle whorl**, with **4,620
registered input images**, one foreground mask per image, and original COLMAP
calibration and sparse geometry.

This is an application dataset accompanying *Prior Augmented Reconstruction
for Objects under Partial Surface Observations*. The meshes are reconstruction
and completion outputs, **not independently measured geometric ground truth**.

## Download

The Git repository contains documentation, indexes, hashes and small tools.
Images and models are provided as two assets in the same repository's
[v1.0.0 Release](https://github.com/Xpx00/Dawenkou-Digitization/releases/tag/v1.0.0):

| Asset | Content | Approximate size |
|---|---|---:|
| `dawenkou41-models-v1.0.0.zip` | 41 PLY meshes, 41 GLB models, per-object metadata | 140 MiB |
| `dawenkou41-multiview-v1.0.0.zip` | Images, masks, COLMAP binary models, readable camera poses and view indexes | 601 MiB |

```bash
git clone https://github.com/Xpx00/Dawenkou-Digitization.git
cd Dawenkou-Digitization
python3 scripts/download.py --component all
python3 -m pip install -r requirements.txt
python3 scripts/verify_dataset.py
```

For models alone, use `--component models` in both commands. Model-only
verification and downloading use Python's standard library. NumPy and Pillow
are needed only for the multiview checks. **Cloning the repository alone does
not download the data.** The downloader verifies the archives and every
extracted file against recorded SHA256 hashes.

## Layout after downloading

```text
objects/
  DWK_0001/                    # consecutive release ID
    model.ply                  # original colored mesh, double coordinates
    model.glb                  # same geometry/vertex color, float32 coordinates
    metadata.json              # original ID, artifact name, axes, branch, hashes
    images/frame_*.jpg          # actual reconstruction input images
    masks/frame_*.jpg.png       # one exact original foreground mask per image
    sparse/0/
      cameras.bin
      images.bin
      points3D.bin
      rigs.bin
      frames.bin
    cameras.json               # readable intrinsics and bidirectional poses
    views.csv                  # image-to-mask and registration correspondence
  ...
  DWK_0041/
metadata/                      # tracked indexes, data hashes and recipe
scripts/                       # preparation, download and validation
```

Each object folder is a standard `images/` + `sparse/0/` COLMAP dataset.
The generated `points3D.ply` duplicate was removed: use `points3D.bin` as the
authoritative sparse geometry; loaders may regenerate their own PLY cache.
The mask naming is the original view-index convention, including `.jpg.png`.

## IDs and preservation

Release IDs run consecutively from `DWK_0001` to `DWK_0041`, sorted by the
original numeric ID. **Release IDs are different from the previous research
IDs.** Use [id_mapping.csv](metadata/id_mapping.csv) to translate them.
For example, original `DWK_0073` is release `DWK_0022`, and original `DWK_0040`
(the stone artifact) is release `DWK_0013`.

Only object folders, model filenames and index paths have been reorganized.
Input image names and the COLMAP binary contents are unchanged. PLY/GLB,
images, selected masks and camera JSON are byte-identical to their source
files. There is no new reconstruction, simplification, resampling, rotation,
registration or scaling in this release.

## Coordinates and scientific scope

- Meshes and cameras share each object's original SfM coordinate frame.
  `X_camera = R @ X_world + t`; camera axes point right, down and forward.
  Quaternion order is `w,x,y,z`.
- The object-specific `up_axis` and `front_axis` are in `metadata.json`.
  Do not assume world Y is the object's vertical direction.
- There is **no common calibrated physical scale**. SfM units are not
  millimetres, and object sizes cannot be directly compared in these units.
- Hidden bottom geometry and transferred color are inferred completion,
  not measured observations. Watertightness does not validate wall thickness,
  semantic openings, unseen shape accuracy or suitability for printing.
- The accepted collection contains **33 envelope-constrained Poisson (HVE)**
  outputs and **8 standard Poisson (T0)** outputs. These are source branches of
  selected models, not comparative success rates.
- The collection is curated and manually reviewed. It has no independent
  train/validation/test split and is not the complete original acquisition cohort.

The data permit inspection of accepted models and reconstruction from the
provided views, masks and sparse calibration. They do **not** include frozen
VGGT-Ω caches, Gaussian checkpoints, source TSDF meshes or the full PAR training
runtime, so exact replay of the historical completed meshes requires those
separate artifacts. See [reproduction scope](docs/REPRODUCTION.md) and
[completion parameters](metadata/completion_recipe.json).

## Validation

`scripts/verify_dataset.py` checks file hashes, continuous IDs, mesh header/color
attributes, image/mask dimensions, COLMAP binary-to-JSON pose correspondence
and inverse camera matrices. The original model hashes preserve the
[recorded accepted-model validation](metadata/model_validation.json).
The script does not perform a new self-intersection audit or measure hidden
surface accuracy.

## License and attribution

This release is licensed under **[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)**:
give attribution, identify modifications, and use the material for
non-commercial purposes. The full legal text is in [LICENSE](LICENSE).

Attribution: **Xpx00, Dawenkou Digitization: Curated Watertight 41, v1.0.0**,
with a link to this repository and the license. `Xpx00` is the publishing
account; no museum affiliation or additional institutional authorship is asserted.
See [CITATION.cff](CITATION.cff). No DOI has been assigned.
