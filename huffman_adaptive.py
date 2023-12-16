import argparse, heapq
from pathlib import Path
from collections import Counter
from hurry.filesize import size


class HuffmanAdaptive:
	encoded_file_extension = '.huff_a'
	chunk_size = 2 ** 12

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
		self.source_f = None

		self.destination = None
		self.destination_f = None

		self.decode = None
		self.n = None
		self.type = None

		self.split_padding = 0
		self.normal_padding = 0

		self.source_data = None
		self.source_index = 0
		self.source_length = 0

		self.destination_data = None

		self.huffman_tree = None

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
		self.parser.add_argument('-n', help='Limit for table action in the form of 2^n bytes', type=int, default=8)
		self.parser.add_argument('-t', help='Type of action to take', choices=['freeze', 'reconstruct', 'normalize'],
		                         default='freeze')
		self.parser.add_argument('-p', '--Print', help='Print flag', action='store_true')
		self.args = self.parser.parse_args()

		self.source = self.args.Source
		self.destination = self.args.Destination
		self.n = self.args.n
		self.type = self.args.t
		self.print = self.args.Print

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

		self.source_data = ''
		self.source_index = 0
		self.source_length = 0

		while chunk := self._read_source_chunk():
			self.source_data += chunk
			self.source_length += len(chunk)

			if self.print:
				print(f'{chunk = }')
				print(f'{self.source_data = }')
				print(f'({self.source_index = } / {self.source_length = })')

		self.print_stats()

	def _decode(self):
		self.print_stats()

	def _read_source_chunk(self):
		if not self.source_f:
			self.source_f = self.source.open('rb')

		return ''.join(bin(byte)[2:].zfill(8) for byte in self.source_f.read(HuffmanAdaptive.chunk_size))

	def _write_destination_chunk(self, encode_padding: bool = False):
		if not self.destination_f:
			self.destination_f = self.destination.open('wb')

		self.destination_f.write(bytearray(self._normalize_bytes(encode_padding)))

	def _normalize_bytes(self, encode_padding: bool = False) -> [int]:
		# join all encoded bytes as a long bit string
		all_bytes = ''.join(self.destination_data)
		all_length = len(all_bytes)

		# calculate right-padding to be able to split all_bytes into 8-bit bytes
		if encode_padding:
			self.normal_padding = (8 - all_length % 8) % 8
			all_bytes += '0' * self.normal_padding
			# if we're encoding, encode split_padding and normal_padding as the [4:12] bits of the header
			all_bytes = (bin(self.split_padding)[2:].zfill(4) + bin(self.normal_padding)[2:].zfill(4)).join(
				[all_bytes[:4], all_bytes[12:]])
			self.destination_data = list()
		else:
			all_length = all_length - (all_length % 8)
			self.destination_data = all_bytes[all_length:]

		if self.print:
			print(f'{all_bytes = }')
		# return a list of bytes split every 8 bits, parsed back into integers
		return [int(all_bytes[i:i + 8], 2) for i in range(0, all_length, 8)]

	def _init_tree(self):
		pass

	def _recalc_tree(self):
		pass

	def _init_table(self):
		pass

	def _recalc_table(self):
		pass

	def print_stats(self):
		s_size = self.source.stat().st_size
		d_size = self.destination.stat().st_size
		print(f'Source file:      {size(s_size)}')
		print(f'Destination file: {size(d_size)}')
		print(f'Compression:      {(s_size - d_size) / s_size * 100:.2f}%')


if __name__ == '__main__':
	HuffmanAdaptive().run()
