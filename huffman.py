import argparse, heapq
from pathlib import Path
from collections import Counter


class Huffman:
    # our chosen file extension
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

    @staticmethod
    def split_bytes(file_bytes: str, byte_size: int) -> [int]:
        return [file_bytes[i:i + byte_size] for i in range(0, len(file_bytes), byte_size)]

    @staticmethod
    def normalize_bytes(encoded_bytes: [str]) -> [int]:
        all_bytes = ''.join(encoded_bytes)
        return [int(all_bytes[i:i + 8].ljust(8, '0'), 2) for i in range(0, len(all_bytes), 8)]

    def __init__(self):
        self.parser = None
        self.args = None
        self.source = None
        self.destination = None
        self.byte_size = None
        self.decode = None

        self.huffman_tree = None
        self.huffman_table = None

    def run(self):
        self._parse_args()
        if self.decode:
            self._decode()
        else:
            self._encode()

    def _parse_args(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('Source', help='Source file')
        self.parser.add_argument('-d', '--Destination', help='Destination file')
        self.parser.add_argument('-D', '--Decode', help='Decode flag', action='store_true')
        self.parser.add_argument('-b', '--ByteSize', help='Size of a byte', default=8, type=int, choices=range(2, 17))
        self.args = self.parser.parse_args()

        self.source = self.args.Source
        self.destination = self.args.Destination
        self.byte_size = self.args.ByteSize
        self.decode = self.args.Decode

        # additional checks for files
        self.source = Path(self.source)
        if not self.source.exists():
            self.parser.error(f'Source file {self.source} does not exist')

        if self.decode:
            if self.source.suffix != Huffman.encoded_file_extension:
                self.parser.error(
                    f'Wrong source file extension for decoding: {self.source.suffix}\n'
                    f'Expected source file extension for decoding: {Huffman.encoded_file_extension}'
                )

            # check destination
            if self.destination is None:
                self.parser.error(f'Destination is required for decoding')

            self.destination = Path(self.destination)
        else:
            # assume name
            if self.destination is None:
                self.destination = self.source.stem + Huffman.encoded_file_extension
            self.destination = Path(self.destination)

            # in case destination was not None, check extension
            if self.destination.suffix != Huffman.encoded_file_extension:
                self.parser.error(
                    f'Wrong destination file extension for encoding: {self.destination.suffix}\n'
                    f'Expected destination file extension for encoding: {Huffman.encoded_file_extension}'
                )

    def _read_source_bytes(self):
        return ''.join(bin(byte)[2:].zfill(8) for byte in self.source.read_bytes())

    def _build_huffman_tree(self, data):
        frequency = Counter(data)
        heap = [Huffman.Node(char, freq) for char, freq in frequency.items()]
        heapq.heapify(heap)

        while len(heap) > 1:
            node1 = heapq.heappop(heap)
            node2 = heapq.heappop(heap)

            merged = Huffman.Node(None, node1.freq + node2.freq)
            merged.left = node1
            merged.right = node2

            heapq.heappush(heap, merged)

        self.huffman_tree = heap[0]
        return self.huffman_tree

    def _generate_codes(self, node, prefix='', code_dict=None):
        if code_dict is None:
            code_dict = {}

        if node is not None:
            if node.char is not None:
                code_dict[node.char] = prefix
            else:
                self._generate_codes(node.left, prefix + '0', code_dict)
                self._generate_codes(node.right, prefix + '1', code_dict)

        self.huffman_table = code_dict
        return self.huffman_table

    def _compress_huffman_table(self):
        return ''

    def _encode(self):
        print(f'{self.source, self.destination = }')

        # get bytes as ints
        s_bytes = self._read_source_bytes()

        # split bytes by byte_size
        s_bytes_split = Huffman.split_bytes(s_bytes, self.byte_size)
        print(f'{s_bytes_split = }')

        # generate huffman dict
        self._generate_codes(self._build_huffman_tree(s_bytes_split))
        print(f'{self.huffman_table = }')
        print(f'{self.huffman_tree = }')

        # encode
        d_bytes = [self.huffman_table[byte] for byte in s_bytes_split]
        print(f'{d_bytes = }')

        # !!! Add header to d_bytes start before writing to file

        # byte_size: 4 bits
        bin_byte_size = bin(self.byte_size - 1)[2:].zfill(4)
        print(f'{bin_byte_size = }')
        # huffman_table
        bin_huffman_table = self._compress_huffman_table()
        print(f'{bin_huffman_table = }')

        # d_bytes.insert(0, bin_byte_size + bin_huffman_table)

        d_bytes = bytearray(Huffman.normalize_bytes(d_bytes))
        print(f'{d_bytes = }')
        with open(self.destination, 'wb') as f:
            f.write(d_bytes)

    def _decode(self):
        print(f'{self.source, self.destination = }')


if __name__ == '__main__':
<<<<<<< HEAD
    Huffman().run()
=======
    main()
# po destytojo pokalbio
#  atkoduojant gali pasirinkti varda
# pirmam tik tekso perdavimo ilgis???? - parametras
# turi but pasirenkamas neperkompiliuojant programos


# adaptyvus
# argumentai - kodo lentele yra tuscia - sudarom kodo lentele kazkokia pagal nutylejima
# abecele turim zinot is anksto
# kas kiek simobliu rekonstruojam
# dar vienas parametras - pasiekus tam tikro dydzui koda, kad kazkuriuo momentu galima uzsaldyti lentele arba ja nuzudyti ir sukurti is naujo, arba normalizuoti
# orientuotis taip kad - maksimalus daznis pasiekia tam tikra riba - kad sitoj vietoj elgesys gali but dvejopas - arba uzsaldom ir dirbam su uzsaldytu, arba nukillinam ir kuriam per nauja
# galima pasiekus riba visu daznius padalint is dvieju - tada dazniu proporcijos isliks, bet nera garanto kad medis nepasikeis ir tada reikai medi perkurti
# kai dazniai labai dideli - medzio reagavims i pakeitimus pasidaro labai ...... sunki procedura(?)

# parametrai - 1.n , 2.riba, 3.ka daryti pasiekus riba
#  
>>>>>>> 9fc142a (destytojo komentarai)
