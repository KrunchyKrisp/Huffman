import argparse, heapq
import os
from pathlib import Path
from hurry.filesize import size


class HuffmanAdaptive:
	encoded_file_extension = '.huff_a'  # chosen encoded file extension
	chunk_size = 2 ** 12  # 4KB
	normalize_limit = 2 ** 8  # 256
	type_dict = {'freeze': '00', 'reconstruct': '01', 'normalize': '10'}  # encoding for our -t variable

	class Node:
		def __init__(self, char, freq, code):
			self.char = char
			self.freq = freq
			self.code = code
			self.left = None
			self.right = None

		# For comparison of nodes
		def __lt__(self, other):
			# we compare nodes based on freq
			return self.freq < other.freq

		def __repr__(self):
			# debug printing
			return f'Node({self.char}: {self.freq}, {self.code})'

	def __init__(self):
		self.parser = None
		self.args = None

		self.source = None
		self.source_f = None

		self.destination = None
		self.destination_f = None

		self.decode = None
		self.n = None
		self.type = None

		self.normal_padding = 0

		self.destination_data = None

		self.huffman_tree = None
		self.huffman_table = None
		self.huffman_frequencies = None
		self.read_bytes = 0  # _update_frequencies() limit compared to self.n (form of 2 ** n)

		self.frozen = False

		self.chunk_index = 0
		self.chunk_length = 0

		self.print = None

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
		self.parser.add_argument('-n', help='Limit for table action in the form of 2^n bytes', type=int, default=8,
		                         choices=range(0, 16))
		self.parser.add_argument('-t', help='Type of action to take', choices=['freeze', 'reconstruct', 'normalize'],
		                         default='freeze')
		self.parser.add_argument('-p', '--Print', help='Print flag', action='store_true')
		self.parser.add_argument('-D', '--Decode', help='Decode flag', action='store_true')
		self.args = self.parser.parse_args()

		self.source = self.args.Source
		self.destination = self.args.Destination
		self.n = self.args.n
		self.type = self.args.t
		self.print = self.args.Print
		self.decode = self.args.Decode

		# additional checks for files
		self.source = Path(self.source)
		if not self.source.exists():
			self.parser.error(f'Source file {self.source} does not exist')

		if self.n < 0:
			self.parser.error(f'-n ({self.n}) must be non-negative')

		if self.decode:
			if self.source.suffix != HuffmanAdaptive.encoded_file_extension:
				self.parser.error(
					f'Wrong source file extension for decoding: {self.source.suffix}\n'
					f'Expected source file extension for decoding: {HuffmanAdaptive.encoded_file_extension}'
				)

			# check destination
			if self.destination is None:
				self.parser.error(f'Destination is required for decoding')

			self.destination = Path(self.destination)
		else:
			# assume name
			if self.destination is None:
				self.destination = self.source.stem + HuffmanAdaptive.encoded_file_extension
			self.destination = Path(self.destination)

			# in case destination was not None, check extension
			if self.destination.suffix != HuffmanAdaptive.encoded_file_extension:
				self.parser.error(
					f'Wrong destination file extension for encoding: {self.destination.suffix}\n'
					f'Expected destination file extension for encoding: {HuffmanAdaptive.encoded_file_extension}'
				)

	def _encode(self):
		if self.print:
			print(f'{self.source, self.destination = }')

		self.destination_data = list()  # init
		# bin_n (4 bits) + normal_padding (4 bits) + bin_type (2 bits)
		# bin_n + normal_padding will be added after the whole file is finished being encoded
		header = '00000000' + HuffmanAdaptive.type_dict[self.type]
		self.destination_data.append(header)
		if self.print:
			print(f'{self.destination_data = }')

		self.read_bytes = 0
		self._init_frequencies()
		self._generate_codes(self._build_huffman_tree())
		if self.print:
			print(f'{sorted(self.huffman_frequencies.items(), key=lambda x: x[1], reverse=True) = }', end='\n\n')
			print(f'{sorted(self.huffman_table.items(), key=lambda x: (len(x[1]), x[1])) = }', end='\n\n')

		while chunk := self._read_source_chunk_bytes():
			if not self.print:
				print('.', end='', flush=True)
			for byte in chunk:
				self.destination_data.append(self.huffman_table[byte])
				self._update_frequencies(byte)

			if self.print:
				print('=' * 256)
				print(f'{chunk = }', end='\n\n')
				print(f'{sorted(self.huffman_frequencies.items(), key=lambda x: x[1], reverse=True) = }', end='\n\n')
				print(f'{sorted(self.huffman_table.items(), key=lambda x: (len(x[1]), x[1])) = }', end='\n\n')
				print(f'{self.destination_data = }')
				print('=' * 256, end='\n\n')
				pass

			self._write_destination_chunk()

		if self.destination_data:
			if self.print:
				print(f'LEFTOVER {self.destination_data = }')
			self._write_destination_chunk(True)

		# updating the header, first byte only
		self.destination_f.close()
		header = bin(self.n)[2:].zfill(4) + bin(self.normal_padding)[2:].zfill(4)
		if self.print:
			print(f'{header = }')
		self.destination_f = open(self.destination, 'rb+')
		self.destination_f.write(bytearray([int(header, 2)]))

		self.print_stats()

	def _decode(self):
		if self.print:
			print(f'{self.source, self.destination = }', end='\n\n')

		self.destination_data = list()
		self.header = ''
		self.chunk_index = 0
		self._init_frequencies()
		self._generate_codes(self._build_huffman_tree())

		if self.print:
			print(f'{sorted(self.huffman_frequencies.items(), key=lambda x: x[1], reverse=True) = }', end='\n\n')
			print(f'{sorted(self.huffman_table.items(), key=lambda x: x[1]) = }', end='\n\n')

		current_byte = ''
		while chunk := self._read_source_chunk_string():
			if not self.print:
				print('.', end='', flush=True)
			self.chunk_length = len(chunk)
			self.chunk_index = 0
			if self.header == '':  # self.header also signals first chunk
				self.header = chunk[:10]
				self.n = 2 ** int(self.header[:4], 2)
				self.normal_padding = int(self.header[4:8], 2)
				self.type = {v: k for k, v in HuffmanAdaptive.type_dict.items()}[self.header[8:]]
				self.chunk_index = 10
				if self.print:
					print(f'{self.header = }')
					print(f'{self.n = }')
					print(f'{self.normal_padding = }')
					print(f'{self.type = }')

			if self.source_f.read(1) == b'':  # last chunk, need to remove self.normal_padding
				self.chunk_length -= self.normal_padding
				if self.print:
					print(f'LAST CHUNK')
			else:  # otherwise move back by 1
				self.source_f.seek(-1, os.SEEK_CUR)  # ###############| A ###############
				if self.print:
					print(f'NOT LAST CHUNK')

			# decoding using huffman_table
			while self.chunk_index < self.chunk_length:  # S[10010]1010101010101, [10010]S[10101]0101010101
				current_byte += chunk[self.chunk_index]
				self.chunk_index += 1
				if current_byte in self.huffman_table:
					decoded_byte = self.huffman_table[current_byte]
					self._update_frequencies(decoded_byte)
					self.destination_data.append(decoded_byte)
					current_byte = ''

			if self.print:
				print('=' * 256)
				print(f'{chunk[:self.chunk_length] = }', end='\n\n')
				print(f'{sorted(self.huffman_frequencies.items(), key=lambda x: x[1], reverse=True) = }', end='\n\n')
				print(f'{sorted(self.huffman_table.items(), key=lambda x: x[1]) = }', end='\n\n')
				print(f'{self.destination_data = }')
				print('=' * 256, end='\n\n')
				pass

			self._write_destination_chunk(normalize=False)

		if self.destination_data:
			if self.print:
				print(f'LEFTOVER {self.destination_data = }')
			self._write_destination_chunk(True, False)

		self.print_stats()

	def _read_source_chunk_bytes(self):
		if not self.source_f:
			self.source_f = self.source.open('rb')

		return self.source_f.read(HuffmanAdaptive.chunk_size)

	def _write_destination_chunk(self, leftover: bool = False, normalize: bool = True):
		if not self.destination_f:
			self.destination_f = self.destination.open('wb')

		if normalize:
			self.destination_f.write(bytearray(self._normalize_bytes(leftover)))
		else:
			self.destination_f.write(bytearray(self.destination_data))
			self.destination_data = list()

	def _normalize_bytes(self, leftover: bool = False) -> [int]:
		# join all encoded bytes as a long bit string
		all_bytes = ''.join(self.destination_data)  # with header: 0000 0000 ## $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
		all_bytes_len = len(all_bytes)
		if self.print:
			# print(f'{all_bytes = }')
			pass

		if not leftover:
			leftover = len(all_bytes) % 8
			leftover_str = all_bytes[all_bytes_len - leftover:]
			self.destination_data = [leftover_str] if leftover_str else list()
			# return a list of bytes split every 8 bits, parsed back into integers
			return [int(all_bytes[i:i + 8], 2) for i in range(0, all_bytes_len - leftover, 8)]
		else:
			self.normal_padding = (8 - all_bytes_len % 8) % 8
			all_bytes += '0' * self.normal_padding
			# return a list of bytes split every 8 bits, parsed back into integers
			return [int(all_bytes, 2)]

	def _init_frequencies(self):
		self.huffman_frequencies = {k: 0 for k in range(0, 2 ** 8)}

	def _build_huffman_tree(self):
		# init heap [Node(1, 2, None), Node(2, 2, None), Node(3, 1, None)]
		heap = [HuffmanAdaptive.Node(char, freq, None) for char, freq in self.huffman_frequencies.items()]
		# heapify based on Node.__lt__, which sorts by node.freq
		heapq.heapify(heap)

		# while we have more than 1 element
		while len(heap) > 1:
			# pop the 2 smallest (by freq) nodes
			node1 = heapq.heappop(heap)
			node2 = heapq.heappop(heap)

			# create a parent node with summed frequencies
			merged = HuffmanAdaptive.Node(None, node1.freq + node2.freq, None)
			merged.left = node1
			merged.right = node2

			# push parent
			heapq.heappush(heap, merged)

		# heap[0] is the root of the whole tree, save and return it
		self.huffman_tree = heap[0]
		return self.huffman_tree

	def _generate_codes(self, node, prefix='', code_dict=None):
		if code_dict is None:
			code_dict = {}

		if node:  # if we have a node
			if node.char is not None:  # if we're a leaf, assign prefix as the encoding of node.char
				if self.decode:
					code_dict[prefix] = node.char
				else:
					code_dict[node.char] = prefix
			else:  # else we travel left (1), then right (0)
				self._generate_codes(node.left, prefix + '1', code_dict)
				self._generate_codes(node.right, prefix + '0', code_dict)

		# save huffman_table and return it
		self.huffman_table = code_dict
		return self.huffman_table

	def _update_frequencies(self, byte):
		self.huffman_frequencies[byte] += 1
		self.read_bytes += 1

		if self.type == 'normalize' and self.huffman_frequencies[byte] >= HuffmanAdaptive.normalize_limit:
			for key in self.huffman_frequencies:
				self.huffman_frequencies[key] //= 2

		if self.read_bytes == self.n:  # limit is in form of 2 ** n
			self.read_bytes = 0
			match self.type:
				case 'freeze':
					if not self.frozen:
						self._generate_codes(self._build_huffman_tree())
						self.frozen = True
				case 'reconstruct':
					self._generate_codes(self._build_huffman_tree())
				case 'normalize':
					self._generate_codes(self._build_huffman_tree())

	def _read_source_chunk_string(self):
		if not self.source_f:
			self.source_f = self.source.open('rb')

		# split all file bytes by byte, get the binary string representation, remove '0b' start, pad left with 0s
		return ''.join(bin(byte)[2:].zfill(8) for byte in self.source_f.read(HuffmanAdaptive.chunk_size))

	def print_stats(self):
		if self.destination_f:
			self.destination_f.close()
		s_size = self.source.stat().st_size
		d_size = self.destination.stat().st_size
		print()
		print(f'Source file:      {size(s_size)}')
		print(f'Destination file: {size(d_size)}')
		print(f'Compression:      {(s_size - d_size) / s_size * 100:.2f}%')


if __name__ == '__main__':
	HuffmanAdaptive().run()
