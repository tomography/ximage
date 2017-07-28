#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example script for additive manufacturing high speed imaging particle tracking
"""

from __future__ import print_function

import os
import sys
import argparse
import fnmatch
import numpy as np
import tomopy

import pandas as pd
from pandas import DataFrame, Series  # for convenience

import pims
import trackpy as tp
import matplotlib as mpl
import matplotlib.pyplot as plt

import ximage

def main(arg):

    parser = argparse.ArgumentParser()
    parser.add_argument("top", help="top directory where the tiff images are located: /data/")
    parser.add_argument("start", nargs='?', const=1, type=int, default=1, help="index of the first image: 10001 (default 1)")

    args = parser.parse_args()

    top = args.top
    index_start = int(args.start)

    # Total number of images to read
    nfile = len(fnmatch.filter(os.listdir(top), '*.tif'))

    # Read the raw data
    rdata = ximage.load_raw(top, index_start)

    particle_bed_reference = ximage.particle_bed_location(rdata[0])
    print("Particle bed location: ", particle_bed_reference)
    
    # Cut the images to remove the particle bed
    cdata = rdata[:, 0:particle_bed_reference, :]

    # Find the image when the shutter starts to close
    dark_index = ximage.shutter_off(rdata)
    print("Shutter CLOSED on image: ", dark_index)

    # Find the images when the laser is on
    laser_on_index = ximage.laser_on(rdata, particle_bed_reference, alpha=1.00)
    print("Laser ON on image: ", laser_on_index)

    # Set the [start, end] index of the blocked images, flat and dark.
    laser_on_index = 47
    flat_range = [0, 1]
    data_range = [laser_on_index, dark_index]
    dark_range = [dark_index, nfile]

    flat = cdata[flat_range[0]:flat_range[1], :, :]
    proj = cdata[data_range[0]:data_range[1], :, :]
    dark = np.zeros((dark_range[1]-dark_range[0], proj.shape[1], proj.shape[2]))  

    # if you want to use the shutter closed images as dark uncomment this:
    #dark = cdata[dark_range[0]:dark_range[1], :, :]  

    ndata = tomopy.normalize(proj, flat, dark)
    ndata = tomopy.normalize_bg(ndata, air=ndata.shape[2]/2.5)
    ndata = tomopy.minus_log(ndata)
    ximage.slider(ndata[150:160:,:])

    ndata = ximage.scale_to_one(ndata)
    ndata = ximage.sobel_stack(ndata)
    ximage.slider(ndata[150:160:,:])

#    ndata = tomopy.normalize(proj, flat, dark)
#    ndata = tomopy.normalize_bg(ndata, air=ndata.shape[2]/2.5)
#    ndata = tomopy.minus_log(ndata)

#    blur_radius = 3.0
#    threshold = .04
#    nddata = ximage.label(ndata, blur_radius, threshold)

#    f = tp.locate(ndata[100, :, :], 41, invert=True)
#    print(f.head)
#    plt.figure()  # make a new figure
#    tp.annotate(f, ndata[100, :, :]);
#    ximage.slider(nddata)


if __name__ == "__main__":
    main(sys.argv[1:])
