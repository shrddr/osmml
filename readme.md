## Original tiles

These use skew and rotate to augment (which is hardly acceptable for satellite imagery). Also, must be problematic when the lamp is on tile edge. Sometimes imagery offset makes the object appear on a wrong tile, this is probably a major roadblock.

```
tfms = get_transforms(do_flip=False)
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.1, ds_tfms=tfms, size=256)
```

Best I got was 3.9% error

## Expanded tiles

This is where I turn off skew, rotate and zoom, because crop should be sufficient. Turns out crop doesn't work like that and must be turned on explicitly - see below. This however shows the performance with virtually no augmentation.

```
tfms = get_transforms(do_flip=False, max_warp=0, max_zoom=0, max_rotate=0
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.1, ds_tfms=tfms, size=256)
```

432px: 1.3% error

356px: frozen 1ep 3.8% > unfrozen 2ep 1.3-1.7% > 2ep 0.7-1.0%

```
tfms = [[crop(size=256, row_pct=(0,1), col_pct=(0,1))],[]]
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.1, ds_tfms=tfms, size=None)
```

356px: frozen 1ep 4-6% > unfrozen 2ep 0.1-0.4% > 2ep 0.2%

As my set only contains 10k images, this means just 2 incorrect validation results O_o