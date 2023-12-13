import argparse, heapq
from pathlib import Path
from collections import Counter


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
			# debug # printing
			return f'Node({self.char}: {self.freq}, {self.code})'

	def __init__(self):
		self.parser = None
		self.args = None
		self.source = None
		self.destination = None
		self.byte_size = None
		self.decode = None
		self.split_padding = 0
		self.normal_padding = 0

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

	def split_bytes(self, file_bytes: str) -> [str]:
		# calculate right-padding to be able to split file_bytes into byte_size bytes
		pad = ((self.byte_size - len(file_bytes) % self.byte_size) % self.byte_size)
		file_bytes += '0' * pad
		self.split_padding = pad
		# return a list of bit strings split every byte_size
		return [file_bytes[i:i + self.byte_size] for i in range(0, len(file_bytes), self.byte_size)]

	def normalize_bytes(self, encoded_bytes: [str], encode_padding: bool = False) -> [int]:
		# join all encoded bytes as a long bit string
		all_bytes = ''.join(encoded_bytes)

		# calculate right-padding to be able to split all_bytes into 8-bit bytes
		pad = (8 - len(all_bytes) % 8) % 8
		self.normal_padding += pad
		all_bytes += '0' * pad
		if encode_padding:
			# if we're encoding, encode split_padding and normal_padding as the [4:12] bits of the header
			all_bytes = (bin(self.split_padding)[2:].zfill(4) + bin(self.normal_padding)[2:].zfill(4)).join(
				[all_bytes[:4], all_bytes[12:]])
		# print(f'{all_bytes = }')
		# return a list of bytes split every 8 bits, parsed back into integers
		return [int(all_bytes[i:i + 8], 2) for i in range(0, len(all_bytes), 8)]

	def _read_source_bytes(self):
		# split all file bytes by byte, get the binary string representation, remove '0b' start, pad left with 0s
		return ''.join(bin(byte)[2:].zfill(8) for byte in self.source.read_bytes())

	def _build_huffman_tree(self, data):
		# build frequency dict
		frequency = Counter(data)
		# init heap
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

		if node:
			# if we have a node
			if node.char:
				# if we're a leaf, assign prefix as the encoding of node.char
				code_dict[node.char] = prefix
			else:
				# else we travel left (1), then right (0)
				self._generate_codes(node.left, prefix + '1', code_dict)
				self._generate_codes(node.right, prefix + '0', code_dict)

		# save huffman_table and return it
		self.huffman_table = code_dict
		return self.huffman_table

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

		if node:
			# if we have a node
			if node.char:
				# if we're a leaf node, we append 1 and node.char to the code
				code += '1' + node.char
			else:
				# else we're not a leaf but have 2 child nodes, append 0, go left, then right
				left, right = node.left, node.right
				code += '0'
				code = Huffman.encode_tree(left, code)
				code = Huffman.encode_tree(right, code)

		return code

	def _compress_huffman_table(self):
		# calling recursive method
		return Huffman.encode_tree(self.huffman_tree)

	def _encode(self):
		# print(f'{self.source, self.destination = }')

		# get bytes as bit string (adds split_padding)
		s_bytes = self._read_source_bytes()
		# print(f'{s_bytes = }')

		# split bytes by byte_size
		s_bytes_split = self.split_bytes(s_bytes)
		# print(f'{s_bytes_split = }')

		# generate huffman_tree and huffman_table
		self._generate_codes(self._build_huffman_tree(s_bytes_split))
		# print(f'{self.huffman_table = }')
		# print(f'{self.huffman_tree = }')

		# encode using huffman_table
		d_bytes = [self.huffman_table[byte] for byte in s_bytes_split]
		# print(f'{d_bytes = }')

		# !!! Add header to d_bytes start before writing to file

		# byte_size: 4 bits, encoding: -1, decoding: +1
		bin_byte_size = bin(self.byte_size - 1)[2:].zfill(4)
		# print(f'{bin_byte_size = }')
		# huffman_table
		bin_huffman_table = self._compress_huffman_table()
		# print(f'{bin_huffman_table = }')

		# byte_size (4bits) + split_padding (4bits) + normal_padding (4bits) + compressed huffman_table
		d_bytes.insert(0, bin_byte_size + '00000000' + bin_huffman_table)
		# print(f'{d_bytes = }')

		# normalizes d_bytes into 8-bit bytes, adds normal_padding, encodes split and normal padding into header
		d_bytes = self.normalize_bytes(d_bytes, True)
		# print(f'{d_bytes = }')

		# writing to file
		with open(self.destination, 'wb') as f:
			f.write(bytearray(d_bytes))

	def _uncompress_huffman_table(self, data: str, node):
		if data:
			# if we still have data left
			if data[0] == '0':
				# if the next bit is 0 we're not in a leaf node
				# get code of current node or ''
				code = node.code if node.code else ''
				# when encoding we always go left (1) then right (0)
				node.left = Huffman.Node(None, None, code + '1')
				node.right = Huffman.Node(None, None, code + '0')

				data = self._uncompress_huffman_table(data[1:], node.left)
				data = self._uncompress_huffman_table(data, node.right)
			else:
				# else we're in a leaf node, read char
				node.char = data[1:1 + self.byte_size]
				return data[1 + self.byte_size:]

		return data

	def _decode(self):
		# print(f'{self.source, self.destination = }')

		# get bytes as bit string
		s_bytes = self._read_source_bytes()
		# print(f'{s_bytes = }')

		# byte_size: first 4 bits, encoding: -1, decoding: +1
		self.byte_size = int(s_bytes[:4], 2) + 1
		# print(f'{self.byte_size = }')

		# split_padding: next 4 bits
		self.split_padding = int(s_bytes[4:8], 2)
		# print(f'{self.split_padding = }')

		# normal_padding: next 4 bits
		self.normal_padding = int(s_bytes[8:12], 2)
		# print(f'{self.normal_padding = }')

		# setup empty root node
		self.huffman_tree = Huffman.Node(None, None, '')
		# get remaining s_bytes after decompressing huffman table bits into huffman_tree
		s_bytes = self._uncompress_huffman_table(s_bytes[12:], self.huffman_tree)
		# print(f'{s_bytes = }')
		# print(f'{self.huffman_tree = }')

		# read huffman_table (in reverse code: char) from flattened huffman_tree, where nodes are leaves
		self.huffman_table = {node.code: node.char for node in Huffman.flatten_tree(self.huffman_tree) if
		                      node.char is not None}
		# print(f'{self.huffman_table = }')

		d_bytes = []
		# fixing normal_padding (added in encoding at the end to fit 8-bit bytes)
		s_bytes = s_bytes[:len(s_bytes) - self.normal_padding]
		# print(f'{s_bytes[:len(s_bytes)-self.normal_padding] = }')

		# decoding using huffman_table
		current_byte = ''
		read_length = 0
		s_bytes_len = len(s_bytes)
		while read_length + len(current_byte) < s_bytes_len:
			current_byte += s_bytes[read_length + len(current_byte)]
			if current_byte in self.huffman_table:
				d_bytes.append(self.huffman_table[current_byte])
				read_length += len(current_byte)
				current_byte = ''

		# print(f'{d_bytes = }')

		# fixing split_padding (added in encoding at the start, when splitting source bytes into byte_size)
		d_bytes[-1] = d_bytes[-1][:len(d_bytes[-1]) - self.split_padding]
		# print(f'{d_bytes = }')

		# normalizing d_bytes into 8-bit bytes for writing
		d_bytes = self.normalize_bytes(d_bytes)
		# print(f'{d_bytes = }')

		# writing to file
		with open(self.destination, 'wb') as f:
			f.write(bytearray(d_bytes))


if __name__ == '__main__':
	Huffman().run()
