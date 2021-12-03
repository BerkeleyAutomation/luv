import os
import numpy as np
import os.path as osp
import fcvision.pytorch_utils as ptu


import torch
from torch.utils.data import Dataset
import torchvision.transforms.functional as TF
import random


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
        image =  TF.affine(image, angle, translate, scale, [0, 0])
        target = TF.affine(target, angle, translate, scale, [0, 0])
    if random.random() > 0.8:
        image = TF.hflip(image)
        target = TF.hflip(target)
    if random.random() > 0.8:
        image = TF.vflip(image)
        target = TF.vflip(target)

    return image, target


class KPDataset:

    def __init__(self, dataset_dir="data/cable_images_labeled", val=False):
        self.dataset_dir = dataset_dir
        self.datapoints = [f for f in os.listdir(self.dataset_dir) if "image" in f]
        self.val = val
        if self.val:
            self.datapoints = self.datapoints[:10]
        else:
            self.datapoints = self.datapoints[10:]


    def __getitem__(self, idx):
        im_file = self.datapoints[idx]
        im = np.load(osp.join(self.dataset_dir, im_file))
        new_im = np.zeros([3, im.shape[1], im.shape[2]])
        new_im[0] = np.copy(im[0])
        new_im[1:] = im
        im = new_im
        target_file = im_file.replace("image", "target")
        target = np.load(osp.join(self.dataset_dir, target_file))[np.newaxis,:,:]

        im, target = target_transforms(im, target)

        if self.val:
            return ptu.torchify(im)
        return ptu.torchify(im, target)


    def __len__(self):
        return len(self.datapoints)