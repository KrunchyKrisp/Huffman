import argparse, heapq
from pathlib import Path
from collections import Counter


class HuffmanAdaptive:
	encoded_file_extension = '.huff_a'

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
		self.decode = None
		self.split_padding = 0
		self.normal_padding = 0

		self.source_data = None
		self.source_index = 0
		self.source_length = 0

		self.destination_data = None

		self.huffman_tree = None

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
		self.args = self.parser.parse_args()

		self.source = self.args.Source
		self.destination = self.args.Destination

		# additional checks for files
		self.source = Path(self.source)
		if not self.source.exists():
			self.parser.error(f'Source file {self.source} does not exist')

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
		pass

	def _decode(self):
		pass


if __name__ == '__main__':
	HuffmanAdaptive().run()
