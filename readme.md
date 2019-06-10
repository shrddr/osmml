## What's up?

These scripts prepare the data to teach a classification network which tells apart satellite imagery tiles with [streetlamp](https://wiki.openstreetmap.org/wiki/Tag:highway%3Dstreet_lamp)s or with no streetlamps. 

The tests below only use the latest and the clearest imagery layer for my location. The dataset contains 10000 samples with 5000 in each category. The training uses resnet34 with fast.ai library. Every run starts with top layers frozen, 1 epoch train to learn the categories. After that follows an `unfreeze` call and training continues until the validation error stabilizes.

## Original tiles

### First attempt

Satellite imagery providers serve data in 256x256 tiles. The first approach is just fetch a tile which contains a lamp and use that as a positive example. Every tile that does not contain a high-level road (highway=tertiary and up) is supposed to be negative.

The problem is some lamps are at the tile edge and possibly cross the boundary. Sometimes [imagery offset](https://wiki.openstreetmap.org/wiki/Using_Imagery#Frequent_mistakes) makes the object appear on a different tile than it should, which produces false positive example.

```
tfms = get_transforms(do_flip=False)
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.1, ds_tfms=tfms, size=256)
```

Best I got was 3.1-3.9% validation error and it just doesn't train any further.

### Dealing with *edge* cases

Here I drop all positive examples where the base of street lamp is less than 10px away from tile edge. Dealing with offset is tricky, as it depends on both imagery properties and OSM mappers in the area. I did eyeball an average offset for my area, but for other cities it can be anything. You can use `video.py` to do that, it lets you look through lots of imagery quickly.

Negative examples are still one random non-road tile.

This dataset converges to 3% error.

## Expanded tiles

### It's compicated

The best thing about satellite imagery is that it's huge and can be scrolled in every direction almost infinitely. If you need more information about a location you can always look at adjacent tiles. This method just fetches a larger square of N pixels around every known streetlamp. These will get randomly cropped later in training process. Negative examples are expanded too, just for consistency.

```
# warning! read below
tfms = get_transforms(do_flip=False, max_warp=0, max_zoom=0, max_rotate=0)
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.2, ds_tfms=tfms, size=256)
```

The results are... questionable:

|       | Frozen, 1 epoch train | Unfreeze, 2 epochs | 2 more epochs |
| ----- | --------------------- | ------------------ | ------------- |
| 256px | 1.9-2.3%              | 1.1-2.1%           | 1.0-1.8%      |
| 356px | 3.7%                  | 3.9%               | 3.7%          |
| 432px | 3.7%                  | 3.6%               | 3.3%          |

The thing is, when I looked closer, all these runs had input data _resized_, not _cropped_ to 256px, which means no augmentation. Both training and validation lamps are in the middle which means the convnet is trained to detect a single dark line in the center of image which is trivial.

### Magic?

Just some mysterious stuff I discovered by accident.

```
tfms = get_transforms(do_flip=False, max_warp=0, max_zoom=0, max_rotate=0)
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.2, ds_tfms=tfms, size=None)
```

This setup leads to exceptional results:

|       | Frozen, 1 epoch train | Unfreeze, 2 epochs | 2 more epochs |
| ----- | --------------------- | ------------------ | ------------- |
| 354px | 2.6-3.8%              |                    |               |
| 356px | 0.3-0.8%              | 0.25-0.35%         | 0.2-0.3%      |
| 356px | 0.5%-1.1%             |                    |               |
| 358px | 1.5%                  |                    |               |

One specific input size is doing too well. 0.2% over 2000 validation images only gives 4 incorrect guesses! There's no way my data is THAT clean. I did generate another batch of images of same size, and it also works wonders.

I have no idea what's going on, but it stops with any other `size` parameter value. Even though the training timing with `size=None` suggests it is done with 299px images. Need to dig into fast.ai code to find the root cause.

### The right way

Training set cropping seems important for real-life applications, because input at inference time will include streetlamps at any part of a tile, not just center of it. The intuition behind that is the network should encounter as much variance in train data as possible. Validation is also cropped randomly to enforce accurate error calculation. Random cropping turned out tricky in fast.ai, here's what I came up with:

```
# crops random 256x256 piece out of larger 
# input image both at train and validation
tfms = [[crop(size=256, row_pct=(0,1), col_pct=(0,1))],
        [crop(size=256, row_pct=(0,1), col_pct=(0,1))]]
data = ImageDataBunch.from_folder(path, train=".", valid_pct=0.1, ds_tfms=tfms, size=None)
```

Results:

|       | Frozen, 1 epoch train | Unfreeze, 2 epochs | 2 more epochs | 4 more |
| ----- | --------------------- | ------------------ | ------------- | ------ |
| 256px | 1.8%                  | 1.4%               | 1.4%          |        |
| 356px | 4.5-4.8%              | 3.0-4.0%           | 3.3-3.9%      | 3.8%   |
| 432px | 4.8%                  | 4.4%               | 4.6%          | 3.7%   |
| 512px | 6.5%                  | 5.9%               | 5.5%          | 4.3%   |

(to be continued)