import argparse
from pathlib import Path
import heapq
from collections import Counter, defaultdict

encoded_file_extension = '.huff'


class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    # For comparison of nodes
    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree(data):
    frequency = Counter(data)
    heap = [Node(char, freq) for char, freq in frequency.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)

        merged = Node(None, node1.freq + node2.freq)
        merged.left = node1
        merged.right = node2

        heapq.heappush(heap, merged)

    return heap[0]


def generate_codes(node, prefix='', code_dict=None):
    if code_dict is None:
        code_dict = {}

    if node is not None:
        if node.char is not None:
            code_dict[node.char] = prefix
        generate_codes(node.left, prefix + '0', code_dict)
        generate_codes(node.right, prefix + '1', code_dict)

    return code_dict


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


def normalize_bytes(encoded_bytes: [bytes]) -> [int]:
    result = []
    current = ''
    while encoded_bytes:
        while encoded_bytes and len(current) < 8:
            current += encoded_bytes.pop(0)
        if len(current) < 8:
            current += '0' * (8 - len(current))
        result.append(int(current[:8], 2))
        current = current[8:]
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
    res = generate_codes(build_huffman_tree(s_bytes_split))
    print(f'{res = }')
    d_bytes = [res[byte] for byte in s_bytes_split]
    print(f'{d_bytes = }')
    d_bytes = bytearray(normalize_bytes(d_bytes))
    print(f'{d_bytes = }')
    with open(destination, 'wb') as f:
        f.write(d_bytes)


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
