#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example script 
"""

from __future__ import print_function
import hspeed
import os
import sys
import argparse
import fnmatch

def main(arg):

    parser = argparse.ArgumentParser()
    parser.add_argument("top", help="top directory where the tiff images are located: /data/")
    parser.add_argument("start", nargs='?', const=1, type=int, default=1, help="index of the first image: 10001 (default 1)")

    args = parser.parse_args()

    top = args.top
    index_start = int(args.start)

    # Read the raw data
    rdata = hspeed.load_raw(top, index_start)

    particle_bed_reference = hspeed.particle_bed_location(rdata[0], plot=False)
    print("Particle bed location: ", particle_bed_reference)
    
    # Cut the images to remove the particle bed
    cdata = rdata[:, 0:particle_bed_reference, :]

    # Find the image when the shutter starts to close
    dark_index = hspeed.shutter_off(rdata)
    print("Shutter CLOSED on image: ", dark_index)

    # Find the images when the laser is on
    laser_on_index = hspeed.laser_on(rdata, particle_bed_reference, alpha=0.8)
    print("Laser ON on image: ", laser_on_index)

if __name__ == "__main__":
    main(sys.argv[1:])