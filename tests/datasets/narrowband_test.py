#!/usr/bin/env python3

# testing narrowband rewrite

from torchsig.datasets.dataset_metadata import NarrowbandMetadata
from torchsig.datasets.narrowband import NewNarrowband, StaticNarrowband
from torchsig.utils.writer import DatasetCreator
from torchsig.signals.signal_lists import TorchSigSignalLists
from torchsig.transforms.target_transforms import (
    ClassName,
    Start,
    Stop,
    LowerFreq,
    UpperFreq,
    SNR,
    YOLOLabel
)
from torchsig.transforms.dataset_transforms import Spectrogram

import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from pathlib import Path


import os
import shutil


# yaml_file = "yaml_narrowband_test.yaml"

# number of samples to test generation
num_samples = 10
save_num_signals = 5

# signals to simulate
class_list = TorchSigSignalLists.all_signals

# distribution of classes
class_dist = np.ones(len(class_list))/len(class_list)

# always generate a signal
num_signals_min = 1

seed = 123456789

# FFT/spectrogram params
fft_size = np.random.randint(128,1024)
num_iq_samples_dataset = fft_size*np.random.randint(128,1024)

# testing to handle cases in which number of samples is not an integer multiple of FFT size
num_iq_samples_dataset += np.random.randint(0,fft_size)

# works for variable sample rates
sample_rate = 10e6

# minimum and maximum SNR for signals
snr_db_max = 50
snr_db_min = 0

# min and max center freq for signals
signal_center_freq_min = -sample_rate/10
signal_center_freq_max = sample_rate/10

# define impairment level
impairment_level = 2

target_transform = [
    ClassName(),
    Start(),
    Stop(),
    LowerFreq(),
    UpperFreq(),
    SNR(),
    YOLOLabel()
]

# set up path to cache directory
root = Path.joinpath(Path(__file__).parent,'narrowband_test')
image_path = f"{root}/images_impaired_{impairment_level}"

def main():
    if os.path.exists(root):
        shutil.rmtree(f"{root}")
    os.makedirs(root, exist_ok=True)
    os.makedirs(image_path, exist_ok=True)

    # build the narrowband metadata
    md = NarrowbandMetadata(
        num_iq_samples_dataset=num_iq_samples_dataset,
        sample_rate=sample_rate,
        fft_size=fft_size,
        num_samples=num_samples,
        num_signals_min=num_signals_min,
        snr_db_max=snr_db_max,
        snr_db_min=snr_db_min,
        signal_center_freq_max=signal_center_freq_max,
        signal_center_freq_min=signal_center_freq_min,
        transforms=Spectrogram(fft_size=fft_size),
        target_transforms=target_transform,
        impairment_level=impairment_level,
        class_list=class_list,
        class_distribution=class_dist,
        seed=seed,
    )

    # create the narrowband object, derived from the metadata object
    NB = NewNarrowband(
        dataset_metadata=md
    )

    # save dataset to disk
    dc = DatasetCreator(
        NB,
        root = root,
        # overwrite=True
    )

    dc.create()

    # load dataset from disk
    NBS = StaticNarrowband(
        root = root,
        impairment_level = impairment_level,
    )

    # inspect and save save_num_signals as images
    for i in tqdm(range(save_num_signals), desc = "Saving as Images"):
        
        data, targets = NBS[i] # runs narrowband's __getitem__
        # print(targets)

        fig = plt.figure(figsize=(18,12))
        ax = fig.add_subplot(1,1,1)
        xmin = 0
        xmax = 1
        ymin = -sample_rate / 2
        ymax = sample_rate / 2
        pos = ax.imshow(data,extent=[xmin,xmax,ymin,ymax],aspect='auto',cmap='Wistia',vmin=md.noise_power_db)
        fig.colorbar(pos, ax=ax)

        # for t in targets:
        classname = targets[0]
        start = targets[1]
        stop = targets[2]
        lower = targets[3]
        upper = targets[4]
        snr = targets[5]
        yololabel = targets[6]


        ax.plot([start,start],[lower,upper],'b',alpha=0.5)
        ax.plot([stop, stop],[lower,upper],'b',alpha=0.5)
        ax.plot([start,stop],[lower,lower],'b',alpha=0.5)
        ax.plot([start,stop],[upper,upper],'b',alpha=0.5)
        textDisplay = str(classname) + ', SNR = ' + str(snr) + ' dB'
        ax.text(start,lower,textDisplay, bbox=dict(facecolor='w', alpha=0.5, linewidth=0))
        ax.set_xlim([0,1])
        ax.set_ylim([-sample_rate/2,sample_rate/2])

        fig.suptitle(f"class: {classname}", fontsize=16)


        plt.savefig(f"{image_path}/{i}")
        plt.ylabel("Frequency (Hz)")
        plt.xlabel("Time")
        plt.close()

if __name__=='__main__':
    main()
    









