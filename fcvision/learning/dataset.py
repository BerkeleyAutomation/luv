import os
import numpy as np
import os.path as osp
import fcvision.utils.pytorch_utils as ptu

import torch
import torchvision.transforms.functional as TF
import random
import cv2


def build_dataset(dataset_cfg):
    dataset_dir = dataset_cfg["dataset_dir"]
    dataset_val = dataset_cfg["val"]
    transform = dataset_cfg["transform"]
    cache = dataset_cfg["cache"] if "cache" in dataset_cfg else False
    dataset = FCDataset(
        dataset_dir=dataset_dir, val=dataset_val, transform=transform, cache=cache
    )
    return dataset


def target_transforms(image, target):
    image = torch.Tensor(image)
    target = torch.Tensor(target)
    if random.random() > 0.8:
        angle = random.randint(-30, 30)
        image = TF.rotate(image, angle)
        target = TF.rotate(target, angle)
    if random.random() > 0.8:
        angle = random.randint(0, 90)
        translate = list(np.random.uniform(0.1, 0.3, 2))
        scale = np.random.uniform(0.75, 0.99)
        image = TF.affine(image, angle, translate, scale, [0, 0])
        target = TF.affine(target, angle, translate, scale, [0, 0])
    if random.random() > 0.8:
        image = TF.hflip(image)
        target = TF.hflip(target)
    if random.random() > 0.8:
        image = TF.vflip(image)
        target = TF.vflip(target)

    # image = image + np.random.uniform(0, 0.1, image.shape)
    image = TF.adjust_brightness(image, np.random.uniform(0.5, 1.5))
    image = TF.adjust_contrast(image, np.random.uniform(0.85, 1.15))

    if random.random() > 0.8:
        image = TF.rgb_to_grayscale(image, 3)

    return image, target


class FCDataset:

    """
    From now on, make sure that dataset_dir has two directories: images and targets.
    Each contain numpy arrays of the form "image_X.npy" and "target_X.npy", where X
    is an integer.
    """

    def __init__(self, dataset_dir, val, transform, cache=False):
        self.dataset_dir = dataset_dir
        self.val = val
        self.transform = transform
        if cache:
            self.cache = {}
        else:
            self.cache = None

        self.image_fnames = os.listdir(osp.join(self.dataset_dir, "images"))
        if self.val:
            self.image_fnames = self.image_fnames[:10]
        else:
            self.image_fnames = self.image_fnames[10:]
        self.mask_fnames = [f.replace("image", "target") for f in self.image_fnames]

    def __getitem__(self, idx):
        im_file = self.image_fnames[idx]
        if not self.val:
            target_file = self.mask_fnames[idx]

        if self.cache and idx in self.cache:
            if not self.val:
                im, target = self.cache[idx]
            else:
                im = self.cache[idx]
        else:
            im = np.load(osp.join(self.dataset_dir, "images", im_file))
            if ".npz" in im_file:
                im_data = im["arr_0"]
                im.close()
                im = im_data
            if not self.val:
                target = np.load(osp.join(self.dataset_dir, "targets", target_file))
                if ".npz" in target_file:
                    target_data = target["arr_0"]
                    target.close()
                    target = target_data
            if self.cache:
                if not self.val:
                    self.cache[idx] = im, target
                else:
                    self.cache[idx] = im

        #DELETE THESE TWO LINES BELOW
        im=cv2.resize(im,(640,480))
        if not self.val:
            target=cv2.resize(target,(640,480))

        im = np.transpose(im, (2, 0, 1))
        if im.max() > 1.0:
            im = im / 255.0
        if not self.val and target.max() > 1.0:
            target = target / 255.0
        if not self.val and len(target.shape) == 2:
            target = target[np.newaxis, :, :]

        if self.transform:
            if self.val:
                im = target_transforms(im)
            else:
                im, target = target_transforms(im, target)

        if self.val:
            return ptu.torchify(im)
        return ptu.torchify(im, target)

    def __len__(self):
        return len(self.image_fnames)
