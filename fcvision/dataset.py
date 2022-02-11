import os
import numpy as np
import os.path as osp
import fcvision.pytorch_utils as ptu

from PIL import Image
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

    # image = image + np.random.uniform(0, 0.1, image.shape)
    image = TF.adjust_brightness(image, np.random.uniform(0.5, 1.5))
    image = TF.adjust_contrast(image, np.random.uniform(0.85, 1.15))

    return image, target


class KPDataset:

    def __init__(self, dataset_dir="data/cable_images_labeled", val=False):
        self.dataset_dir = dataset_dir
        self.datapoints = [f for f in os.listdir(self.dataset_dir) if "image" in f and "uv" not in f]
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
        new_im[1] = np.copy(im[0])
        new_im[2] = np.copy(im[0])
        # new_im[1:] = im
        im = new_im
        target_file = im_file.replace("image", "target")

        target = np.load(osp.join(self.dataset_dir, target_file))
        if len(target.shape) == 2:
            target = target[np.newaxis,:,:]

        im, target = target_transforms(im, target)

        if self.val:
            return ptu.torchify(im)
        return ptu.torchify(im, target)

    def __len__(self):
        return len(self.datapoints)


class CableSegDataset:

    def __init__(self, dataset_dir="data/cable_red_painted_images", val=False):
        self.dataset_dir = dataset_dir
        self.datapoints = [f for f in os.listdir(self.dataset_dir) if "image" in f and "uv" not in f]
        self.val = val
        if self.val:
            self.datapoints = [f for f in self.datapoints if int(f.split(".")[0].split("_")[1]) < 5]
            # self.datapoints = self.datapoints[:10]
        else:
            self.datapoints = [f for f in self.datapoints if int(f.split(".")[0].split("_")[1]) >= 5]
            # self.datapoints = self.datapoints[10:]


    def __getitem__(self, idx):
        im_file = self.datapoints[idx]
        im = np.array(Image.open(osp.join(self.dataset_dir, im_file)))
        # new_im = np.zeros([3, im.shape[1], im.shape[2]])
        target_file = im_file.replace("image", "mask").replace("_", "_full_") # train on full red/green masks
        target = np.array(Image.open(osp.join(self.dataset_dir, target_file)))
        # target = np.load(osp.join(self.dataset_dir, target_file))
        im = np.transpose(im, (2, 0, 1))
        if len(target.shape) == 2:
            target = target[np.newaxis,:,:]
        target[target > 0] = 1.0
        im, target = target_transforms(im, target)

        if self.val:
            return ptu.torchify(im)
        return ptu.torchify(im, target)

    def __len__(self):
        return len(self.datapoints)


class KPConcatDataset:

    def __init__(self, dataset_dir="data/cable_images_labeled", val=False):
        self.dataset_dir1 = "data/cable_images_labeled"
        self.dataset_dir2 = "data/cable_images_overhead_labeled"
        self.datapoints = [osp.join(self.dataset_dir1, f) for f in os.listdir(self.dataset_dir1) if "image" in f]
        self.datapoints = self.datapoints + [osp.join(self.dataset_dir2, f) for f in os.listdir(self.dataset_dir2) if "image" in f]
        self.val = val
        if self.val:
            self.datapoints = self.datapoints[:10]
        else:
            self.datapoints = self.datapoints[10:]


    def __getitem__(self, idx):
        im_file = self.datapoints[idx]
        im = np.load(im_file)
        new_im = np.zeros([3, im.shape[1], im.shape[2]])
        new_im[0] = np.copy(im[0])
        new_im[1] = np.copy(im[0])
        new_im[2] = np.copy(im[0])
        # new_im[1:] = im
        im = new_im
        target_file = im_file.replace("image_", "target_")

        target = np.load(target_file)
        if len(target.shape) == 2:
            target = target[np.newaxis,:,:]

        im, target = target_transforms(im, target)

        if self.val:
            return ptu.torchify(im)
        return ptu.torchify(im, target)

    def __len__(self):
        return len(self.datapoints)


class KPVectorDataset:

    def __init__(self, dataset_dir="data/cable_vecs", val=False):
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
        target = np.load(osp.join(self.dataset_dir, target_file))

        im, target = target_transforms(im, target)

        if self.val:
            return ptu.torchify(im)
        return ptu.torchify(im, target)

    def __len__(self):
        return len(self.datapoints) 


class StereoSegDataset:

    def __init__(self, dataset_dir="data/cloth_images_processed", val=False):
        self.dataset_dir = dataset_dir
        self.datapoints = [f for f in os.listdir(self.dataset_dir) if ("image" in f and not "uv" in f)]
        self.val = val
        if self.val:
            self.datapoints = self.datapoints[:10]
        else:
            self.datapoints = self.datapoints[10:]


    def __getitem__(self, idx):
        im_file = self.datapoints[idx]
        im = np.array(Image.open(osp.join(self.dataset_dir, im_file)))
        im = np.transpose(im, (2, 0, 1))
        # im = np.load(osp.join(self.dataset_dir, im_file))
        target_file = im_file.replace("image", "mask")
        target_file = target_file.replace(".png", ".npy")
        target = np.load(osp.join(self.dataset_dir, target_file))[np.newaxis,:,:]

        im, target = target_transforms(im, target)

        if self.val:
            return ptu.torchify(im)
        return ptu.torchify(im, target)


    def __len__(self):
        return len(self.datapoints)
