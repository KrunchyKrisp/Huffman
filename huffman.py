import os
import argparse
from pathlib import Path

encoded_file_extension = '.huff'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('Source', help='Source file')
    parser.add_argument('-d', '--Destination', help='Destination file')
    parser.add_argument('-D', '--Decode', help='Decode flag', action='store_true')
    parser.add_argument('-b', '--ByteSize', help='Size of a byte', default=8, type=int, choices=range(2, 17))
    args = parser.parse_args()

    print(args)
    source = Path(args.Source)
    destination = args.Destination

    # encoding
    if args.Decode:
        # check source extension
        if source.suffix != encoded_file_extension:
            print(f'Wrong source file extension for decoding: {source.suffix}')
            print(f'Expected source file extension for decoding: {encoded_file_extension}')
            exit()
        # check destination
        if destination is None:
            # need to figure out original extension? maybe different flow overall
            destination = source.stem + '.???'
        destination = Path(destination)

    # encoding
    else:
        # assume name
        if destination is None:
            destination = source.stem + encoded_file_extension
        destination = Path(destination)
        # in case destination was not None, check extension
        if destination.suffix != encoded_file_extension:
            print(f'Wrong destination file extension for encoding: {destination.suffix}')
            print(f'Expected destination file extension for encoding: {encoded_file_extension}')
            exit()

    # reading/writing
    with source.open('rb') as s_file:
        with destination.open('wb') as d_file:
            while s_buffer := s_file.read(16):
                print(s_buffer)
