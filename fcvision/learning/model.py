import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision.utils import save_image
import pytorch_lightning as pl
import matplotlib.pyplot as plt
import numpy as np
import torchvision
import random

import os
from torchvision.models.segmentation import fcn_resnet50
from torchvision.utils import save_image

from fcvision.learning.losses import *
from fcvision.learning.unet_model import UNet

def process_checkpoint(ckpt):
    # original saved file with DataParallel
    old_dict = torch.load(ckpt)
    state_dict = old_dict['state_dict']
    # create new OrderedDict that does not contain `module.`
    from collections import OrderedDict
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        name = k.replace("module.", "")
        new_state_dict[name] = v
    old_dict['state_dict'] = new_state_dict
    return old_dict

def build_PL_model(cfg, train=False, loss=None, checkpoint=None):
    if train:
        params = {
            "num_classes": cfg["num_classes"],
            "loss": loss,
            "optim_learning_rate": cfg["optimizer"]["optim_learning_rate"],
            "weight_decay":cfg['optimizer']['weight_decay'],"decay_gamma":cfg['optimizer']['decay_gamma'],
            'backbone':cfg['backbone']
        }
        return PlModel(params)
    else:
        assert checkpoint is not None
        params = {
                "loss": None,'backbone':cfg['backbone'],
            "num_classes": cfg["num_classes"]
        }
        return PlModel.load_from_checkpoint(checkpoint, params=params).eval().cuda()


class PlModel(pl.LightningModule):
    def __init__(self, params, logdir=None):
        '''
        backbone can be "UNET" or "FCN50"
        '''
        super().__init__()

        self.save_hyperparameters()
        self.params = params
        self.set_logdir(logdir)
        if params['backbone']=='FCN50':
            self.model = fcn_resnet50(
                pretrained=False, progress=False, num_classes=params["num_classes"]
            )
        elif params['backbone']=='UNET':
            self.model = UNet(3,params['num_classes'])
        # self.model = nn.DataParallel(self.model)
        self.loss_fn = params["loss"]

    def set_logdir(self, logdir):
        if logdir is not None:
            self.vis_dir = os.path.join(logdir, "vis")
            self.vis_counter = 0
            try:
                os.makedirs(self.vis_dir)
            except FileExistsError:
                pass
        else:
            self.vis_dir = None
            self.vis_counter = None

    def forward(self, img):
        encoding_dict = self.model(img)
        out = encoding_dict["out"]
        return out

    def training_step(self, batch, batch_idx):
        ims, targets = batch

        preds = self(ims)

        loss_sm = self.loss_fn(preds, targets)
        self.log(
            "Loss", loss_sm, on_step=True, on_epoch=True, prog_bar=True, logger=True
        )
        self.log("train/loss", loss_sm)
        return loss_sm

    def validation_step(self, batch, batch_idx):
        ims = batch
        preds = self(ims)
        return {"ims": ims, "preds": preds}

    def validation_epoch_end(self, outputs):
        if self.vis_dir is None:
            return

        idx = self.vis_counter
        self.vis_counter += 1
        if idx % 1 or not len(outputs):
            return
        outputs = outputs[0]
        for j in range(len(outputs["ims"])):
            im = outputs["ims"][j]
            pred = torch.sigmoid(outputs["preds"][j])
            if self.params["num_classes"] > 1:
                pred = pred[0]  # temporary, for kp-vec prediction
            save_image(im, os.path.join(self.vis_dir, "%d_%d_im.png" % (idx, j)))
            save_image(pred, os.path.join(self.vis_dir, "%d_%d_pred.png" % (idx, j)))
            save_image(
                pred + im, os.path.join(self.vis_dir, "%d_%d_overlayed.png" % (idx, j))
            )
            self.logger.log_image(key=f"val_{j}", images=[im, pred, pred + im], caption=["Input", "Pred", "Overlayed"])

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(
            self.parameters(), lr=self.params["optim_learning_rate"],weight_decay=self.params['weight_decay']
        )
        scheduler=torch.optim.lr_scheduler.ExponentialLR(optimizer,gamma = self.params['decay_gamma'])
        return [optimizer],[scheduler]
