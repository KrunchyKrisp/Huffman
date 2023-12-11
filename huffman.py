import os
import argparse
from pathlib import Path

encoded_file_extension = '.huff'


def parse_args_decode(source: str, destination: str) -> (Path, str):
    # check source extension
    source = Path(source)
    if source.suffix != encoded_file_extension:
        print(f'Wrong source file extension for decoding: {source.suffix}')
        print(f'Expected source file extension for decoding: {encoded_file_extension}')
        exit()
    # check destination
    if destination is None:
        destination = source.stem

    return source, destination


def parse_args_encode(source: str, destination: str) -> (Path, Path):
    # assume name
    source = Path(source)
    if destination is None:
        destination = source.stem + encoded_file_extension
    destination = Path(destination)
    # in case destination was not None, check extension
    if destination.suffix != encoded_file_extension:
        print(f'Wrong destination file extension for encoding: {destination.suffix}')
        print(f'Expected destination file extension for encoding: {encoded_file_extension}')
        exit()

    return source, destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('Source', help='Source file')
    parser.add_argument('-d', '--Destination', help='Destination file')
    parser.add_argument('-D', '--Decode', help='Decode flag', action='store_true')
    parser.add_argument('-b', '--ByteSize', help='Size of a byte', default=8, type=int, choices=range(2, 17))
    args = parser.parse_args()

    print(args)
    source = args.Source
    destination = args.Destination

    # Path, str (find out original extension from header)
    if args.Decode:
        source, destination = parse_args_decode(source, destination)
    # Path, Path (checked)
    else:
        source, destination = parse_args_encode(source, destination)
