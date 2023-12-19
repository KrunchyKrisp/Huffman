import argparse, heapq
import time
from pathlib import Path
from collections import Counter
from hurry.filesize import size
from tabulate import tabulate


class Huffman:
	# our chosen file extension
	encoded_file_extension = '.huff'

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
			# debug if self.print:printing
			return f'Node({self.char}: {self.freq}, {self.code})'

	@staticmethod
	def flatten_tree(node, heap=None):
		if heap is None:
			heap = []
		if node:
			# if we have a node, traverse post-order
			if node.left:
				Huffman.flatten_tree(node.left, heap)
			if node.right:
				Huffman.flatten_tree(node.right, heap)
			heap.append(node)
		return heap

	@staticmethod
	def encode_tree(node, code=None):
		if code is None:
			code = ''

		if node:  # if we have a node
			if node.char:  # if we're a leaf node, we append 1 and node.char to the code
				code += '1' + node.char
			else:  # else we're not a leaf but have 2 child nodes, append 0, go left, then right
				left, right = node.left, node.right
				code += '0'
				code = Huffman.encode_tree(left, code)
				code = Huffman.encode_tree(right, code)

		return code

	def __init__(self):
		self.parser = None
		self.args = None
		self.source = None
		self.destination = None
		self.byte_size = None
		self.decode = None
		self.split_padding = 0
		self.normal_padding = 0

		self.source_data = None
		self.source_index = 0
		self.source_length = 0

		self.destination_data = None

		self.huffman_tree = None
		self.huffman_table = None

		self.print = None

	def run(self):
		start = time.perf_counter()
		self._parse_args()
		if self.decode:
			self._decode()
		else:
			self._encode()
		end = time.perf_counter()
		self.print_stats(end - start)

	def _parse_args(self):
		self.parser = argparse.ArgumentParser()
		self.parser.add_argument('Source', help='Source file')
		self.parser.add_argument('-d', '--Destination', help='Destination file')
		self.parser.add_argument('-D', '--Decode', help='Decode flag', action='store_true')
		self.parser.add_argument('-b', '--ByteSize', help='Size of a byte', default=8, type=int, choices=range(2, 17))
		self.parser.add_argument('-p', '--Print', help='Print flag', action='store_true')
		self.args = self.parser.parse_args()

		self.source = self.args.Source
		self.destination = self.args.Destination
		self.byte_size = self.args.ByteSize
		self.decode = self.args.Decode
		self.print = self.args.Print

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

	def _encode(self):
		if self.print:
			print(f'{self.source, self.destination = }')

		# get bytes as bit string
		self.source_data = self._read_source_bytes()
		if self.print:
			print(f'{self.source_data = }')

		# split bytes by byte_size (adds split_padding)
		self.source_data = self._split_bytes()
		if self.print:
			print(f'{self.source_data = }')

		# generate huffman_tree and huffman_table
		self._generate_codes(self._build_huffman_tree())
		if self.print:
			print(f'{self.huffman_table = }')
			print(f'{self.huffman_tree = }')

		# encode using huffman_table
		self.destination_data = [self.huffman_table[byte] for byte in self.source_data]
		if self.print:
			print(f'{self.destination_data = }')

		# !!! Add header to d_bytes start before writing to file

		# byte_size: 4 bits, encoding: -1, decoding: +1
		bin_byte_size = bin(self.byte_size - 1)[2:].zfill(4)
		if self.print:
			print(f'{bin_byte_size = }')
		# split_padding: 4 bits
		bin_split_padding = bin(self.split_padding)[2:].zfill(4)
		if self.print:
			print(f'{bin_split_padding = }')
		# huffman_table
		bin_huffman_table = self._compress_huffman_table()
		if self.print:
			print(f'{bin_huffman_table = }')

		# byte_size (4bits) + split_padding (4bits) + normal_padding (4bits) (inserted in _normalize_bytes) + compressed huffman_table
		self.destination_data.insert(0, bin_byte_size + bin_split_padding + '' + bin_huffman_table)
		if self.print:
			print(f'{self.destination_data = }')

		# normalizes d_bytes into 8-bit bytes, adds normal_padding, encodes split and normal padding into header
		self.destination_data = self._normalize_bytes(self.destination_data, True)
		if self.print:
			print(f'{self.destination_data = }')

		# writing to file
		with open(self.destination, 'wb') as f:
			f.write(bytearray(self.destination_data))

	def _decode(self):
		if self.print:
			print(f'{self.source, self.destination = }')

		# get bytes as bit string
		self.source_data = self._read_source_bytes()
		self.source_index = 0
		self.source_length = len(self.source_data)
		if self.print:
			print(f'{self.source_data = }')

		# byte_size: first 4 bits, encoding: -1, decoding: +1
		self.byte_size = int(self.source_data[:4], 2) + 1
		if self.print:
			print(f'{self.byte_size = }')

		# split_padding: next 4 bits
		self.split_padding = int(self.source_data[4:8], 2)
		if self.print:
			print(f'{self.split_padding = }')

		# normal_padding: next 4 bits
		self.normal_padding = int(self.source_data[8:12], 2)
		if self.print:
			print(f'{self.normal_padding = }')

		# setup empty root node
		self.huffman_tree = Huffman.Node(None, None, '')
		# get remaining s_bytes after decompressing huffman table bits into huffman_tree
		self.source_index = 12
		self._uncompress_huffman_tree(self.huffman_tree)
		if self.print:
			print(f'{self.source_data[self.source_index:] = }')
			print(f'{self.huffman_tree = }')

		# read huffman_table (in reverse code: char) from flattened huffman_tree, where nodes are leaves
		self.huffman_table = {node.code: node.char for node in Huffman.flatten_tree(self.huffman_tree) if node.char}
		if self.print:
			print(f'{self.huffman_table = }')

		self.destination_data = []
		# fixing normal_padding (added in encoding at the end to fit 8-bit bytes) 10101010 1111[0000]
		self.source_length -= self.normal_padding
		# s_bytes = s_bytes[:len(s_bytes) - self.normal_padding]
		if self.print:
			print(f'{self.source_data[self.source_index:self.source_length] = }')

		# decoding using huffman_table
		current_byte = ''
		while self.source_index < self.source_length:  # S[10010]1010101010101, [10010]S[10101]0101010101
			current_byte += self.source_data[self.source_index]
			self.source_index += 1
			if current_byte in self.huffman_table:
				self.destination_data.append(self.huffman_table[current_byte])
				current_byte = ''

		if self.print:
			print(f'{self.destination_data = }')

		# fixing split_padding (added in encoding at the start, when splitting source bytes into byte_size)
		# 11000 -> 11
		self.destination_data[-1] = self.destination_data[-1][:len(self.destination_data[-1]) - self.split_padding]
		if self.print:
			print(f'{self.destination_data = }')

		# normalizing d_bytes into 8-bit bytes for writing
		self.destination_data = self._normalize_bytes(self.destination_data)
		if self.print:
			print(f'{self.destination_data = }')

		# writing to file
		with open(self.destination, 'wb') as f:
			f.write(bytearray(self.destination_data))

	def _read_source_bytes(self):
		# split all file bytes by byte, get the binary string representation, remove '0b' start, pad left with 0s
		return ''.join(bin(byte)[2:].zfill(8) for byte in self.source.read_bytes())

	def _split_bytes(self) -> [str]:
		# calculate right-padding to be able to split file_bytes into byte_size bytes
		self.split_padding = ((self.byte_size - len(self.source_data) % self.byte_size) % self.byte_size)
		self.source_data += '0' * self.split_padding
		# return a list of bit strings split every byte_size
		return [self.source_data[i:i + self.byte_size] for i in range(0, len(self.source_data), self.byte_size)]

	def _build_huffman_tree(self):
		# build frequency dict [1, 1, 2, 2, 3] -> {1: 2, 2: 2, 3: 1}
		frequency = Counter(self.source_data)
		# init heap [Node(1, 2, None), Node(2, 2, None), Node(3, 1, None)]
		heap = [Huffman.Node(char, freq, None) for char, freq in frequency.items()]
		# heapify based on Node.__lt__, which sorts by node.freq
		heapq.heapify(heap)

		# while we have more than 1 element
		while len(heap) > 1:
			# pop the 2 smallest (by freq) nodes
			node1 = heapq.heappop(heap)
			node2 = heapq.heappop(heap)

			# create a parent node with summed freqs
			merged = Huffman.Node(None, node1.freq + node2.freq, None)
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
			if node.char:  # if we're a leaf, assign prefix as the encoding of node.char
				code_dict[node.char] = prefix
			else:  # else we travel left (1), then right (0)
				self._generate_codes(node.left, prefix + '1', code_dict)
				self._generate_codes(node.right, prefix + '0', code_dict)

		# save huffman_table and return it
		self.huffman_table = code_dict
		return self.huffman_table

	def _compress_huffman_table(self):
		# calling recursive method
		return Huffman.encode_tree(self.huffman_tree)

	def _normalize_bytes(self, encoded_bytes: [str], encode_padding: bool = False) -> [int]:
		# join all encoded bytes as a long bit string
		all_bytes = ''.join(encoded_bytes)

		# calculate right-padding to be able to split all_bytes into 8-bit bytes
		# we do +4 if we encode_padding to account for the 4 bits that normal_padding is going to take up in the header
		self.normal_padding = (8 - (len(all_bytes) + (4 if encode_padding else 0)) % 8) % 8
		all_bytes += '0' * self.normal_padding
		if encode_padding:
			# if we're encoding, encode split_padding and normal_padding as the [4:12] bits of the header
			bin_normal_padding = bin(self.normal_padding)[2:].zfill(4)
			if self.print:
				print(f'{bin_normal_padding = }')
			# byte_size (4bits) + split_padding (4bits) + normal_padding (4bits) + compressed huffman_table + data
			all_bytes = all_bytes[:8] + bin_normal_padding + all_bytes[8:]
		if self.print:
			print(f'{all_bytes = }')
		# return a list of bytes split every 8 bits, parsed back into integers
		return [int(all_bytes[i:i + 8], 2) for i in range(0, len(all_bytes), 8)]

	def _uncompress_huffman_tree(self, node: Node):
		if self.source_index < self.source_length:  # if we still have data left
			if self.source_data[self.source_index] == '0':  # if the next bit is 0 we're not in a leaf node
				# get code of current node or ''
				code = node.code if node.code else ''
				# when encoding we always go left (1) then right (0)
				node.left = Huffman.Node(None, None, code + '1')
				node.right = Huffman.Node(None, None, code + '0')

				self.source_index += 1
				self._uncompress_huffman_tree(node.left)
				self._uncompress_huffman_tree(node.right)
			else:  # == '1'. else we're in a leaf node, read char.       1[#####]0001[#####]00
				node.char = self.source_data[self.source_index + 1: self.source_index + 1 + self.byte_size]
				self.source_index += 1 + self.byte_size

	def print_stats(self, total_time):
		s_size = self.source.stat().st_size
		d_size = self.destination.stat().st_size
		table = [
			['Source file', size(s_size)],
			['Destination file', size(d_size)],
			['Decompression' if self.decode else 'Compression', f'{(((d_size - s_size) / s_size + 1) if self.decode else ((s_size - d_size) / s_size)) * 100:.2f}%'],
			['Total time', f'{total_time:.2f}s']
		]
		print(tabulate(table))


if __name__ == '__main__':
	Huffman().run()
