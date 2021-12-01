import torchvision.transforms as transforms

import numpy as np
import os

import torch
from torch.utils.data import DataLoader
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint
import matplotlib.pyplot as plt
import numpy as np

from src.dataset import KPDataset
from src.model import PlModel
from src.arg_utils import parse_args
# from torchvision import models
import src.run_utils as ru



def main():

    params = parse_args()

    logdir = ru.get_file_prefix(params)
    os.makedirs(os.path.join(logdir, 'lightning_logs'))

    if params['seed'] != -1:
        pl.seed_everything(params['seed'])
        np.random.seed(params['seed'])

    dataset = KPDataset()
    dataset_val = KPDataset(val=True)


    im = dataset[1]
    batch_size = 6
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=params['loader_n_workers'])
    loader_val = DataLoader(dataset_val, batch_size=12, num_workers=params['loader_n_workers'])

    model = PlModel(params, logdir)

    trainer = pl.Trainer(
        default_root_dir=logdir,
        gpus=params['n_gpus'],
        max_epochs=params['epochs'],
        callbacks=[ModelCheckpoint(dirpath=os.path.join(logdir, 'models'))]
        # plugins=pl.plugins.training_type.ddp.DDPPlugin(find_unused_parameters=False),
    )
    trainer.fit(model, loader, loader_val)



if __name__ == '__main__':
    main()