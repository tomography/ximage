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
alignment module for ximage
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import sys
import os
import argparse

from scipy.optimize import least_squares
from skimage.filters import threshold_li
from skimage.io import imread
from skimage.feature import register_translation
from skimage.transform import AffineTransform, warp, FundamentalMatrixTransform
import numpy as np

__authors__ = "Mark Wolfman"
__copyright__ = "Copyright (c) 2017, Argonne National Laboratory"
__version__ = "0.0.1"
__all__ = ['alignment_pass',
           'transform_image',
           'image_corrections']


def alignment_pass(img, img_180):
    upsample = 200
    # Register the translation correction
    trans = register_translation(img, img_180, upsample_factor=upsample)
    trans = trans[0]
    # Register the rotation correction
    lp_center = (img.shape[0] / 2, img.shape[1] / 2)
    # lp_center = (0, 0)
    img_ft = np.fft.fft2(img)
    img_180_ft = np.fft.fft2(img_180)
    img_lp = logpolar_fancy(img, *lp_center)
    img_180_lp = logpolar_fancy(img_180, *lp_center)
    result = register_translation(img_lp, img_180_lp, upsample_factor=upsample)
    scale_rot = result[0]
    angle = np.degrees(scale_rot[1] / img_lp.shape[1] * 2 * np.pi)
    return angle, trans


def _transformation_matrix(r=0, tx=0, ty=0, sx=1, sy=1):
    # Prepare the matrix
    ihat = [ sx * np.cos(r), sx * np.sin(r), 0]
    jhat = [-sy * np.sin(r), sy * np.cos(r), 0]
    khat = [ tx,             ty,             1]
    # Make the eigenvectors into column vectored matrix
    new_transform = np.array([ihat, jhat, khat]).swapaxes(0, 1)
    return new_transform


def transform_image(img, rotation=0, translation=(0, 0)):
    """Take a set of transformations and apply them to the image.
    
    Rotations occur around the center of the image, rather than the
    (0, 0).
    
    Parameters
    ----------
    translation : 2-tuple, optional
      Translation parameters in (vert, horiz) order.
    rotation : float, optional
      Rotation in degrees.
    scale : 2-tuple, optional
      Scaling parameters in (vert, horiz) order.
    
    """
    rot_center = (img.shape[1] / 2, img.shape[0] / 2)
    xy_trans = (translation[1], translation[0])
    M0 = _transformation_matrix(tx=-rot_center[0], ty=-rot_center[1])
    M1 = _transformation_matrix(r=np.radians(rotation), tx=xy_trans[0], ty=xy_trans[1])
    M2 = _transformation_matrix(tx=rot_center[0], ty=rot_center[1])
    M = M2 @ M1 @ M0
    tr = FundamentalMatrixTransform(M)
    out = warp(img, tr)
    return out


def image_corrections(img_name_0, img_name_180, passes=15):
    img = imread(img_name_0)
    img_180 = imread(img_name_180)
    img = np.flip(img, 1)
    cume_angle = 0
    cume_trans = np.array([0, 0], dtype=float)
    for pass_ in range(passes):
        # Prepare the inter-translated images
        working_img = transform_image(img, translation=cume_trans, rotation=cume_angle)
        # Calculate a new transformation
        angle, trans = alignment_pass(working_img, img_180)
        # Save the cumulative transformations
        cume_angle += angle
        cume_trans += np.array(trans)
    # Convert translations to (x, y)
    cume_trans = (-cume_trans[1], cume_trans[0])
    return cume_angle, cume_trans


_transforms = {}

def _get_transform(i_0, j_0, i_n, j_n, p_n, t_n, p_s, t_s):
    transform = _transforms.get((i_0, j_0, i_n, j_n, p_n, t_n))
    if transform == None:
        i_k = []
        j_k = []
        p_k = []
        t_k = []
        for p in range(0, p_n):
            p_exp = np.exp(p * p_s)
            for t in range(0, t_n):
                t_rad = t * t_s
                i = int(i_0 + p_exp * np.sin(t_rad))
                j = int(j_0 + p_exp * np.cos(t_rad))
                if 0 <= i < i_n and 0 <= j < j_n:
                    i_k.append(i)
                    j_k.append(j)
                    p_k.append(p)
                    t_k.append(t)
        transform = ((np.array(p_k), np.array(t_k)), (np.array(i_k), np.array(j_k)))
        _transforms[i_0, j_0, i_n, j_n, p_n, t_n] = transform
    return transform


def logpolar_fancy(image, i_0, j_0, p_n=None, t_n=None):
    (i_n, j_n) = image.shape[:2]
    
    i_c = max(i_0, i_n - i_0)
    j_c = max(j_0, j_n - j_0)
    d_c = (i_c ** 2 + j_c ** 2) ** 0.5
    
    if p_n == None:
        p_n = int(np.ceil(d_c))
    
    if t_n == None:
        t_n = j_n
    
    p_s = np.log(d_c) / p_n
    t_s = 2.0 * np.pi / t_n
    
    (pt, ij) = _get_transform(i_0, j_0, i_n, j_n, p_n, t_n, p_s, t_s)
    
    transformed = np.zeros((p_n, t_n) + image.shape[2:], dtype=image.dtype)
    
    transformed[pt] = image[ij]
    return transformed

