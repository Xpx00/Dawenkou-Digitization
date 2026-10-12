# Dawenkou Digitization 41

41 colored 3D models of Dawenkou artifacts: 40 pottery objects and one stone artifact. The dataset includes 4,620 multiview images, foreground masks and COLMAP reconstructions.

## Download

- [3D models (PLY and GLB)](https://github.com/Xpx00/Dawenkou-Digitization-41/releases/download/v1.0.0/models.zip)
- [Images, masks and camera data](https://github.com/Xpx00/Dawenkou-Digitization-41/releases/download/v1.0.0/multiview.zip)

Download both archives and extract them into the same directory, or run:

```bash
python3 download.py
```

## Structure

```text
objects/
  DWK_0001/
    model.ply
    model.glb
    metadata.json
    images/
    masks/
    sparse/0/
    cameras.json
    views.csv
  ...
  DWK_0041/
```

See [objects.csv](objects.csv) for the artifact list.

## License

[CC BY-NC 4.0](LICENSE).
