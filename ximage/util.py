#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2017, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2015. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

"""
Utility module for ximage
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import fnmatch
import dxchange
import numpy as np

import scipy
import scipy.ndimage as ndi
import skimage as ski

__authors__ = "Francesco De Carlo"
__copyright__ = "Copyright (c) 2017, Argonne National Laboratory"
__version__ = "0.0.1"
__all__ = ['load_raw',
           'shutter_off',
           'particle_bed_location',
           'laser_on',
           'scale_to_one',
           'sobel_stack',
           'label']

def load_raw(top, index_start):
    """
    Load a stack of tiff images.

    Parameters
    ----------
    top : str
        Top data directory.

    index_start : int
        Image index start.

    Returns
    -------
    ndarray
        3D stack of images.
    """
    template = os.listdir(top)[1]

    nfile = len(fnmatch.filter(os.listdir(top), '*.tif'))
    index_end = index_start + nfile
    ind_tomo = range(index_start, index_end)

    fname = top + template

    # Read the tiff raw data.
    rdata = dxchange.read_tiff_stack(fname, ind=ind_tomo)
    return rdata

def shutter_off(image, alpha=0.7):
    """
    Finds the first image with the shutter closed.

    Parameters
    ----------
    image : ndarray
        3D stack of images.

    alpha : float
        Threshold level.

    Returns
    -------
    int
        Index of the first image with the shutter closed.
    """

    flat_sum = np.sum(image[0, :, :])
    nimages = image.shape[0]
    for index in range(nimages):
        image_sum = np.sum(image[index, :, :])
        if image_sum < alpha * flat_sum :
            return index
    return None

def particle_bed_location(image):
    """
    Finds the image row marking the location of the particle bed.

    Parameters
    ----------
    image : ndarray
        2D image.

    Returns
    -------
    int
        Image row marking the location of the particle bed.
    """

    edge = np.sum(image, axis=1)
    x = np.arange(0, edge.shape[0], 1)
    y = ndi.gaussian_filter(edge/float(np.amax(edge)), 5)
    return np.abs(y - 0.5).argmin()

def laser_on(rdata, particle_bed_ref, alpha=1.0):
    """
    Function description.

    Parameters
    ----------
    rdata : ndarray
        3D stack of images.

    particle_bed_ref : int
        Image row marking the location of the particle bed.

    alpha : float
        Threshold level.

    Returns
    -------
    int
        Index of the first image with the laser on.
    """
    nimages = rdata.shape[0]
    status = np.empty(nimages)

    for index in range(nimages):
        ndata = rdata[index]
        edge = np.sum(ndata, axis=1)
        y = ndi.gaussian_filter(edge/float(np.amax(edge)), 5)
        particle_bed = np.abs(y - 0.5).argmin()

        if particle_bed > particle_bed_ref * alpha :
            return index
    return None

def scale_to_one(ndata):
    """
    Scale a stack of images between [0,1].

    Parameters
    ----------
    ndata : ndarray
        3D stack of images.

    Returns
    -------
    ndarray
        3D stack of images.
    """

    ndata_max = np.amax(ndata)
    ndata_min = np.amin(ndata)
    nimages = ndata.shape[0]
    for index in range(nimages):
        # normalize between [0,1]
        ndata_max = np.amax(ndata[index, :, :])
        ndata_min = np.amin(ndata[index, :, :])
        ndata[index, :, :] = (ndata[index, :, :] - ndata_min) / (ndata_max - ndata_min)
    return ndata

def sobel_stack(ndata):
    """
    Applies sobel filter to a stack of images.

    Parameters
    ----------
    ndata : ndarray
        3D stack of images.

    Returns
    -------
    ndarray
        3D stack of images.
    """

    nimages = ndata.shape[0]
    for index in range(nimages):
        ndata[index, :, :] = ski.filters.sobel(ndata[index, :, :])
    return ndata

def label(ndata, blur_radius=1.0, alpha=1):
    """
    Counts the number of particles in a stack of images.

    Parameters
    ----------
    ndata : ndarray
        3D stack of images.

    blur_radius : float
        Gaussian blur radius.

    alpha : float
        Threshold level.

    Returns
    -------
    ndata, nr_objects
        3D stack of images, number of particles per image.
    """


    nimages = ndata.shape[0]
    for index in range(nimages):
        ndata[index, :, :] = ndi.gaussian_filter(ndata[index, :, :], blur_radius)
        ndata[index, :, :], nr_objects = scipy.ndimage.label(ndata[index, :, :] > alpha) 
        print ("Image %d contains %d particles" % (index, nr_objects))
    return ndata, nr_objects
