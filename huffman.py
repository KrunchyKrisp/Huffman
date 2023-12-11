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


def split_byte(current_bytes: int, current_bits: int, byte_size: int) -> (int, int):
    if current_bits > byte_size:
        return current_bytes >> (current_bits - byte_size), current_bytes & ((1 << (current_bits - byte_size)) - 1)
    else:
        return current_bytes << (byte_size - current_bits), 0


def split_bytes(file_bytes: [int], byte_size: int) -> [int]:
    if byte_size == 8:
        return file_bytes

    result = []
    current = 0
    current_bits = 0
    while file_bytes:
        while file_bytes and current_bits < byte_size:
            current = (current << 8) + file_bytes.pop(0)
            current_bits += 8
        left, current = split_byte(current, current_bits, byte_size)
        current_bits -= byte_size
        result.append(left)
    return result


def decode(source, destination):
    # Path, str (find out original extension from header)
    source, destination = parse_args_decode(source, destination)
    print(f'{source, destination = }')


def encode(source, destination, byte_size):
    # Path, Path (checked)
    source, destination = parse_args_encode(source, destination)
    print(f'{source, destination = }')
    s_bytes = [byte for byte in source.read_bytes()]
    s_bytes_split = split_bytes(s_bytes, byte_size)
    print(f'{s_bytes_split = }')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('Source', help='Source file')
    parser.add_argument('-d', '--Destination', help='Destination file')
    parser.add_argument('-D', '--Decode', help='Decode flag', action='store_true')
    parser.add_argument('-b', '--ByteSize', help='Size of a byte', default=8, type=int, choices=range(2, 17))
    args = parser.parse_args()

    print(args)
    source = args.Source
    destination = args.Destination

    if args.Decode:
        decode(source, destination)
    else:
        encode(source, destination, args.ByteSize)


if __name__ == '__main__':
    main()
