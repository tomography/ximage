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
Module for describing .....
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import fnmatch
import dxchange
import numpy as np
import matplotlib as mpl
import matplotlib.pylab as pl
import matplotlib.widgets as wdg
import matplotlib.pyplot as plt

import skimage as ski
import skimage.segmentation as seg
import skimage.morphology as morth
import scipy.ndimage as ndi
import scipy

__authors__ = "First Name Last Name"
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
    Function description.

    Parameters
    ----------
    parameter_01 : type
        Description.

    parameter_02 : type
        Description.

    parameter_03 : type
        Description.

    Returns
    -------
    return_01
        Description.
    """
    template = os.listdir(top)[1]

    nfile = len(fnmatch.filter(os.listdir(top), '*.tif'))
    index_end = index_start + nfile
    ind_tomo = range(index_start, index_end)

    fname = top + template

    # Read the tiff raw data.
    rdata = dxchange.read_tiff_stack(fname, ind=ind_tomo)
    return rdata

def shutter_off(image, alpha=0.7, plot=False):
    """
    Function description.

    Parameters
    ----------
    parameter_01 : type
        Description.

    parameter_02 : type
        Description.

    parameter_03 : type
        Description.

    Returns
    -------
    return_01
        Description.
    """

    flat_sum = np.sum(image[0, :, :])
    nimages = image.shape[0]
    for index in range(nimages):
        image_sum = np.sum(image[index, :, :])
        if image_sum < alpha * flat_sum :
            return index
    return None

def particle_bed_location(image, plot=False):
    """
    Function description.

    Parameters
    ----------
    parameter_01 : type
        Description.

    parameter_02 : type
        Description.

    parameter_03 : type
        Description.

    Returns
    -------
    return_01
        Description.
    """

    edge = np.sum(image, axis=1)
    x = np.arange(0, edge.shape[0], 1)
    y = ndi.gaussian_filter(edge/float(np.amax(edge)), 5)
    if plot:
        plt.plot(x, y)
        plt.show()
    return np.abs(y - 0.5).argmin()

def laser_on(rdata, particle_bed_ref, alpha=1.0):
    """
    Function description.

    Parameters
    ----------
    parameter_01 : type
        Description.

    parameter_02 : type
        Description.

    parameter_03 : type
        Description.

    Returns
    -------
    return_01
        Description.
    """
    nimages = rdata.shape[0]
    status = np.empty(nimages)
    # for index in range(nimages):
    #     ndata = rdata[index]
    #     edge = np.sum(ndata, axis=1)
    #     y = ndi.gaussian_filter(edge/float(np.amax(edge)), 5)
    #     particle_bed = np.abs(y - 0.5).argmin()

    #     if particle_bed <= particle_bed_ref :
    #         status[index] = False
    #     else:
    #         status[index] = True
    #         particle_bed_ref = particle_bed_ref * alpha
    # return status

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
    Function description.

    Parameters
    ----------
    parameter_01 : type
        Description.

    parameter_02 : type
        Description.

    parameter_03 : type
        Description.

    Returns
    -------
    return_01
        Description.
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
    Function description.

    Parameters
    ----------
    parameter_01 : type
        Description.

    parameter_02 : type
        Description.

    parameter_03 : type
        Description.

    Returns
    -------
    return_01
        Description.
    """

    nimages = ndata.shape[0]
    for index in range(nimages):
        ndata[index, :, :] = ski.filters.sobel(ndata[index, :, :])
    return ndata

def label(ndata, blur_radius=1.0, threshold=1):
    """
    Function description.

    Parameters
    ----------
    parameter_01 : type
        Description.

    parameter_02 : type
        Description.

    parameter_03 : type
        Description.

    Returns
    -------
    return_01
        Description.
    """


    nimages = ndata.shape[0]
    for index in range(nimages):
        ndata[index, :, :] = ndi.gaussian_filter(ndata[index, :, :], blur_radius)
        ndata[index, :, :], nr_objects = scipy.ndimage.label(ndata[index, :, :] > threshold) 
        print ("Image %d contains %d particles" % (index, nr_objects))
        # print(np.amin(ndata[index, :, :]), np.amax(ndata[index, :, :]), np.mean(ndata[index, :, :]))
    return ndata, nr_objects
