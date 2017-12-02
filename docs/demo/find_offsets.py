from __future__ import print_function

import os
import sys
import argparse

import ximage

if __name__ == '__main__':
    # Prepare arguments
    parser = argparse.ArgumentParser(
        description='Compare two images and get rotation/translation offsets.')
    parser.add_argument('original_image', help='The original image file')
    parser.add_argument('flipped_image', help='Image of the specimen after 180 deg stage rotation.')
    parser.add_argument('--passes', '-p', help='How many iterations to run.',
                        default=15, type=int)
    args = parser.parse_args()
    # Perform the correction calculation
    rot, trans = ximage.image_corrections(args.original_image, args.flipped_image,
                                   passes=args.passes)
    # Display the result
    msg = "DR: {:.2f} deg, DX: {:.2f} px, DY: {:.2f} px"
    msg = msg.format(rot, trans[0], trans[1])
    print(msg)
