This is a collection of scripts to generate machine learning training images using OpenStreetMap data and satellite imagery providers. I tend to use Maxar](https://github.com/osmlab/editor-layer-index/pull/655) layer because it's recent, crispy, and shot at almost vertical angle. At other locations results may vary.

The training uses resnet34 architecture with fast.ai library.

# Streetlamps

Task: Classify imagery tiles with [streetlamp](https://wiki.openstreetmap.org/wiki/Tag:highway%3Dstreet_lamp)s vs. no streetlamps. 

## Original tiles

### First attempt

Satellite imagery providers serve data in 256x256 tiles. The first approach is just fetch a tile which contains a lamp and use that as a positive example. Every tile that does not contain a high-level road (highway=tertiary and up) is supposed to be negative.

The problem is some lamps are at the tile edge and possibly cross the boundary. Sometimes [imagery offset](https://wiki.openstreetmap.org/wiki/Using_Imagery#Frequent_mistakes) makes the object appear on a different tile than it should, which produces false positive example.

What I did is drop all positive examples where the base of street lamp is less than 16px away from tile edge. Dealing with offset is tricky, as it depends on both imagery properties and OSM mappers in the area. I did eyeball an average offset for my area, but for other cities it can be anything. You can use `video.py` to do that, it lets you look through lots of imagery quickly.

```
from fastai.vision import *
from fastai.metrics import error_rate

path = # script output
tfms = get_transforms(do_flip=False, max_warp=0, max_zoom=0, max_rotate=0)
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.1, ds_tfms=tfms, size=224)
learn = cnn_learner(data, models.resnet34, metrics=error_rate)
# LR is learning rate, use learn.lr_find() to estimate
learn.fit_one_cycle(1, max_lr=7e-2)
learn.unfreeze()
# slice notation means linear increase between deepest and top layer
learn.fit_one_cycle(2, max_lr=slice(2e-6,2e-4))
learn.fit_one_cycle(2, max_lr=slice(4e-7,4e-5))
```

This dataset converges to 3% error. There must be another way to do this!

|      | Frozen, 4 epoch train | Unfreeze, 4 epochs | 4 more   |
| ---- | --------------------- | ------------------ | -------- |
| z18  | 3.6-4.0%              | 3.4-4.0%           | 3.2-3.6% |
| z19  | 4.6-5.3%              | 4.2-4.7%           | 4.1-4.7% |

## Expanded tiles

### It's compicated

The best thing about satellite imagery is that it's huge and can be scrolled in every direction almost infinitely. If you need more information about a location you can always look at adjacent tiles. This method just fetches a larger square of N pixels around every known streetlamp. These will get randomly cropped later in training process. Negative examples are expanded too, just for consistency.

```
# warning! read below
tfms = get_transforms(do_flip=False, max_warp=0, max_zoom=0, max_rotate=0)
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.2, ds_tfms=tfms, size=256)
```

Results:

|       | Frozen, 1 epoch train | Unfreeze, 2 epochs | 2 more epochs |
| ----- | --------------------- | ------------------ | ------------- |
| 356px | 3.7%                  | 3.9%               | 3.7%          |
| 432px | 3.7%                  | 3.6%               | 3.3%          |

The thing is, when I looked closer, all these runs had input data _resized_, not _cropped_ to 256px, which means no augmentation. Both training and validation lamps are in the middle which means the convnet is trained to detect a single dark line in the center of image which is trivial. I would say 3% error is too much for that task.

### Random crop

Training set cropping seems important for real-life applications, because input at inference time will include streetlamps at any part of a tile, not just center of it. The intuition behind that is the network should encounter as much variance in train data as possible. Validation set still contains original tiles. Random cropping turned out tricky in fast.ai, here's what I came up with:

```
# crops random 256x256 piece out of train images;
# validation images are not transformed
tfms = [[crop(size=256, row_pct=(0,1), col_pct=(0,1))], []]
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.1, ds_tfms=tfms, size=None)
```

The problem is, the performance is now worse than before:

|       | Frozen, 1 epoch train | Unfreeze, 2 epochs | 2 more epochs |
| ----- | --------------------- | ------------------ | ------------- |
| 256px | 4.8%                  | 3.9%               | 3.8%          |
| 356px | 5.7%                  | 4.2%               | 3.9%          |
| 432px | 7.3%                  | 5.5%               | 4.7%          |
| 512px | 8.3%                  | 6.4%               | 7.1%          |

### Unexpected magic

Just some mysterious stuff I discovered by accident.

```
tfms = get_transforms(do_flip=False, max_warp=0, max_zoom=0, max_rotate=0)
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.2, ds_tfms=tfms, size=None)
```

No resize and no crop leads to exceptional results:

|       | Frozen, 1 epoch train | Unfreeze, 2 epochs | 2 more epochs |
| ----- | --------------------- | ------------------ | ------------- |
| 354px | 1.0-2.2%              | 2.5%               | 2.4%          |
| 356px | 0.3-0.8%              | 0.25-0.35%         | 0.2-0.3%      |
| 356px | 0.5%-0.6%             | 0.3%               | 0.3%          |
| 358px | 1.0-1.5%              | 0.8%               | 0.8%          |

One specific input size is doing too well. 0.2% over 2000 validation images only gives 4 incorrect guesses! But that is pretty much expected for a task of detecting a dark vertical line. I did generate another batch of images of same size, and it also works wonders. But why is every other input image size performing so much worse?

I have no idea what's going on, but it stops with any other `size` parameter value. Even though the training timing with `size=None` suggests it uses 299px images, `size=299` does not work the same. Looks like the resize is handled in some special way behind the scenes. Need to dig into fast.ai code to find the root cause.

# Roofshapes

Task: classify [roof:shape](https://wiki.openstreetmap.org/wiki/Simple_3D_buildings#Roof_shape)=gabled, hipped, or flat.

Input: varies (see table)

| Input size    | Frozen, 8 epoch train | Unfreeze, 8 epochs | 8 more epochs |
| ------------- | --------------------- | ------------------ | ------------- |
| 712/712/712   | 6.3%                  | 5.6%               | 5.1%          |
| 715/1469/4262 | 5.6%                  | 4.9%               | 4.6%          |
|               | 5.9%                  | 4.9%               | 4.3%          |
| 882/1403/4022 | 4.2%                  | 2.8%               | 3.0%          |
|               | 4.3%                  | 3.6%               | 3.5%          |
|               | 4.9%                  | 3.2%               | 3.0%          |

# Buildings

Task: classify tiles with any type of building(s) vs. tiles with no buildings at all.

Input: 5700 images of both categories, 20% validation

|                              | Frozen, 4 epoch train | Unfreeze, 6 epochs | 8 more epochs |
| ---------------------------- | --------------------- | ------------------ | ------------- |
| 256 no flip no rotation      | 3.0%                  | 3.0%               |               |
| 256 no flip full 20 rotation | 2.3%                  | 2.7%               |               |
| 256 no flip full 40 rotation |                       |                    |               |
|                              |                       |                    |               |
|                              |                       |                    |               |
|                              |                       |                    |               |