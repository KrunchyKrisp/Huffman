import os
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('Source', help='Source file', type=argparse.FileType('rb'))
    parser.add_argument('-d', '--Destination', help='Destination file', type=argparse.FileType('wb'))
    parser.add_argument('-D', '--Decode', help='Decode flag', action='store_true')
    parser.add_argument('-b', '--ByteSize', help='Size of a byte', default=8, type=int)
    args = parser.parse_args()
    print(args)
