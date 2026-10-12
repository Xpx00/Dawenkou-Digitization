# Reproduction scope

## Included evidence

The release contains the accepted mesh outputs and the exact reconstruction
input images, foreground masks, sparse COLMAP geometry and camera poses for
41 objects. Every retained binary/image/model file is byte-identical to the
source package. Changing an object ID does not change its frame names or poses.

Each `objects/DWK_xxxx` folder can be supplied as a standard COLMAP scene root
to software that loads `images/` and `sparse/0/`. `views.csv` supplies the
foreground-mask association. The extra `.jpg` in mask filenames is deliberate.
Do not assume a stem-only mask path without consulting this index.

Keep the camera convention and original world coordinate frame unchanged.
If a viewer needs an upright object, apply a display transform derived from
`up_axis`; do not transform a model without transforming its cameras too.

## Historical processing represented by the models

The original application used Reliable Ω 2DGS optimization for 15,000
iterations followed by TSDF surface extraction and Screened Poisson completion.
The accepted files come from two branches:

- **HVE (33 models):** foreground-envelope-constrained completion.
- **T0 (8 models):** standard Poisson completion.

Both historical completion branches use matched oriented TSDF samples,
Poisson depth 8, scale 1.45, 4 solver iterations and pointWeight 2, with at
most 1,200,000 sample points and seed 20260926. These are the actual recorded
parameters of this curated subset, not a depth-9 recipe.

The HVE envelope used a 128³ grid, 32 direction-spread construction views,
512-pixel mask maximum dimension, 2-pixel guard, at least two-view outside
consensus and dilation 0.06 times the source height. Full registered-view
checks and manual review followed candidate generation. These settings are
recorded in `metadata/completion_recipe.json`; they are not new measurements.

## What this minimal package cannot replay alone

Frozen VGGT-Ω predictions and selected initialization seeds, trained Gaussian
checkpoints, source TSDF surfaces, Poisson oriented-point caches, historical
solver executables and the complete PAR runtime are **not included** here.
These are separate method/runtime artifacts, not duplicate input images.
Consequently this data release supports a fresh reconstruction from the
provided inputs and inspection of the reviewed outputs; it does not establish
bitwise end-to-end reproduction of the historical meshes.

Raw videos are not included. The released images are the actual selected
reconstruction inputs, not an independently sampled video evaluation set.
There is no independent split or measured hidden-bottom ground truth.

## Validation commands

```bash
# All released files and image/camera correspondence
python3 -m pip install -r requirements.txt
python3 scripts/verify_dataset.py --component all

# Models only, without NumPy or Pillow
python3 scripts/verify_dataset.py --component models

# Put a detailed check report outside Git-tracked files
python3 scripts/verify_dataset.py --output verification.local.json
```

The validator reads SHA256 manifests, PLY/GLB geometry counts and color
attributes, COLMAP binary image records and readable poses. Its geometric
validity evidence is the historical accepted-model report bound to unchanged
model hashes. It does not infer unobserved geometry accuracy from topology.
