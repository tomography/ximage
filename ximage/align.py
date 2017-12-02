#!/bin/env python3
from __future__ import print_function

import sys
import os
import argparse

from scipy.optimize import least_squares
from skimage.filters import threshold_li
from skimage.io import imread
from skimage.feature import register_translation
from skimage.transform import AffineTransform, warp, FundamentalMatrixTransform
import numpy as np

#import dxchange
import matplotlib.pyplot as plt


__authors__ = "Mark Wolfman"
__copyright__ = "Copyright (c) 2017, Argonne National Laboratory"
__version__ = "0.0.1"
__all__ = ['alignment_pass',
           'transform_image',
           'image_corrections']

def flip(m, axis):
    if not hasattr(m, 'ndim'):
        m = asarray(m)
    indexer = [slice(None)] * m.ndim
    try:
        indexer[axis] = slice(None, None, -1)
    except IndexError:
        raise ValueError("axis=%i is invalid for the %i-dimensional input array"
                         % (axis, m.ndim))
    return m[tuple(indexer)]


def alignment_pass(img, img_180):
    upsample = 200
    # Register the translation correction
    # print(img.shape)
    # print(img_180.shape)
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
    # python 3.6
    # M = M2 @ M1 @ M0
    MT = np.dot(M1, M0)
    M = np.dot(M2, MT)

    tr = FundamentalMatrixTransform(M)
    out = warp(img, tr)
    return out


def image_corrections(img_name_0, img_name_180, passes=15):
    img = imread(img_name_0)
#    img = dxchange.read_tiff(img_name_0)
    plt.imshow(img, interpolation='nearest', cmap='gray')
    plt.show()
    img_180 = imread(img_name_180)
#    img_180 = dxchange.read_tiff(img_name_180)
    plt.imshow(img_180, interpolation='nearest', cmap='gray')
    plt.show()
    # python 3.6
    # img = np.flip(img, 1)
    img = flip(img, 1)
    cume_angle = 0
    cume_trans = np.array([0, 0], dtype=float)
    for pass_ in range(passes):
        # Prepare the inter-translated images
        working_img = transform_image(img, translation=cume_trans, rotation=cume_angle)
        # Calculate a new transformation
        print(pass_)
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


if __name__ == '__main__':
    # Prepare arguments
    parser = argparse.ArgumentParser(
        description='Compare two images and get rotation/translation offsets.')
    parser.add_argument('original_image', help='The original image file')
    parser.add_argument('flipped_image',
                        help='Image of the specimen after 180° stage rotation.')
    parser.add_argument('--passes', '-p', help='How many iterations to run.',
                        default=15, type=int)
    args = parser.parse_args()
    # Perform the correction calculation
    rot, trans = image_corrections(args.original_image, args.flipped_image,
                                   passes=args.passes)
    # Display the result
    msg = "ΔR: {:.2f}°, ΔX: {:.2f}px, ΔY: {:.2f}px"
    msg = msg.format(rot, trans[0], trans[1])
    print(msg)
