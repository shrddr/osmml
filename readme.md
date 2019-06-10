## What's up?

These scripts prepare the data to teach a classification network which tells apart satellite imagery tiles with [streetlamp](https://wiki.openstreetmap.org/wiki/Tag:highway%3Dstreet_lamp)s or with no streetlamps. The tests only use the latest and the clearest imagery layer for my city called Maxar.

## Original tiles

### First attempt

Satellite imagery providers serve data in 256x256 tiles. The first approach is just fetch a tile which contains a lamp and use that as a positive example. Every tile that does not contain a high-level road (highway=tertiary and up) is supposed to be negative.

The problem is some lamps are at the tile edge and possibly cross the boundary. Sometimes [imagery offset](https://wiki.openstreetmap.org/wiki/Using_Imagery#Frequent_mistakes) makes the object appear on a different tile than it should, which produces false positive example.

```
tfms = get_transforms(do_flip=False)
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.1, ds_tfms=tfms, size=256)
```

Best I got was 3.1-3.9% validation error and it just doesn't train any further.

### Discard "edge cases"

Here I drop all positive examples where the base of street lamp is less than 10px away from tile edge. Dealing with offset is tricky, as it depends on both imagery properties and OSM mappers in the area. I did eyeball an average offset for my area, but for other cities it can be anything. You can use `video.py` to do that, it lets you look through lots of imagery quickly.

Negative examples are still one random non-road tile.

This dataset converges to 3% error.

## Expanded tiles

### Damn it works.. oh wait

The best thing about satellite imagery is that it's huge and can be scrolled in every direction almost infinitely. If you need more information about a location you can always look at adjacent tiles. This method just fetches a larger square of 356 pixels around every known streetlamp. These will get randomly cropped later in training process. Negative examples are expanded to 356px too, just for consistency.

Turns out, these runs had no crop at all - see below. This however shows the performance with virtually no augmentation.

```
# just resizes 356->256px with no crop!
tfms = get_transforms(do_flip=False, max_warp=0, max_zoom=0, max_rotate=0)
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.1, ds_tfms=tfms, size=256)
```

The validation error comes down to:

|       | Deeper layers frozen, 1 epoch train | Unfreeze, 2 epochs | 2 more epochs |
| ----- | ----------------------------------- | ------------------ | ------------- |
| 432px |                                     |                    | 1.3%          |
| 356px | 3.8%                                | 1.3-1.7%           | 0.7-1.0%      |

### The real thing

Train set cropping seems important for real-life applications, because input at inference time will include streetlamps at any part of a tile, not just center of it. That's why we need to crop randomly at train time. Random cropping turned out tricky in fast.ai, here's my hack that looks like it's doing the right thing:

```
# crops random 256x256 piece out of larger 
# input image both at train and validation
tfms = [[crop(size=256, row_pct=(0,1), col_pct=(0,1))],
        [crop(size=256, row_pct=(0,1), col_pct=(0,1))]]
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.1, ds_tfms=tfms, size=None)
```

Results are indeed much better:

|       | Deeper layers frozen, 1 epoch train | Unfreeze, 2 epochs | 2 more epochs |
| ----- | ----------------------------------- | ------------------ | ------------- |
| 356px | 4-6%                                | 0.1-0.4% / 3.4%    | 0.2%          |
| 432px | 4.8-5.5%                            | 3.8-4.7%           | 5.5%          |

As my set only contains 10k images, and validation is 10% of that, 0.1% error means just one incorrect validation result. Oh my.