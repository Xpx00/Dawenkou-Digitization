# Dawenkou Digitization 41

3D meshes of Dawenkou-heritages. The dataset includes 4,620 multiview images, foreground masks and COLMAP reconstructions.

## Download

- [3D models (PLY and GLB)](https://github.com/Xpx00/Dawenkou-Digitization-41/releases/download/v1.0.0/models.zip)
- [Images, masks and camera data](https://github.com/Xpx00/Dawenkou-Digitization-41/releases/download/v1.0.0/multiview.zip)
- [Gaussian models (2DGS PLY)](https://github.com/Xpx00/Dawenkou-Digitization-41/releases/download/v1.1.0/gaussians.zip)
- [32-color print models (3MF)](https://github.com/Xpx00/Dawenkou-Digitization-41/releases/download/v1.1.0/print_32color.zip)

Extract the archives you need into the same directory.

Gaussian PLYs contain 2DGS surfels and need a compatible renderer. The 32-color 3MF copies are scaled to 100 mm in height; select your printer and map the colors to your filaments.

## Structure

```text
objects/
  DWK_0001/
    model.ply
    model.glb
    gaussian.ply
    print_32color.3mf
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
