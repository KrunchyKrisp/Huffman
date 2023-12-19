
# Documentation for Huffman and Huffman Adaptive Compression CLIs

## Introduction

This document provides an overview of two Python-based CLIs:
* Huffman Compression CLI
* Huffman Adaptive Compression CLI

These CLIs implement the Huffman coding algorithm, a method for lossless data compression, with the latter incorporating adaptive techniques for handling dynamic data patterns.


## Huffman Compression CLI

### Overview
The Huffman Compression CLI is a basic implementation of the Huffman coding algorithm. It is suitable for educational purposes and demonstrates the principles of lossless data compression.

### Running the CLI
- **Encoding (Compression):**
  ```
  python3 huffman.py [source_file] -d [destination_file] -p
  ```
- **Decoding (Decompression):**
  ```
  python3 huffman.py [source_file] -d [destination_file] -D -p
  ```

### Key Components
- **Node Class**: Represents a node in the Huffman tree.
- **Huffman Tree**: Used for generating Huffman codes.
- **File Handling**: Reads from and writes to files, handling binary data.
- **Command-Line Interface**: Uses `argparse` for handling command-line arguments.

## Huffman Adaptive Compression CLI

### Overview
The Huffman Adaptive Compression CLI is an advanced version that dynamically updates its Huffman tree based on the input data.

### Running the CLI
- **Encoding:**
  ```
  python3 huffman_adaptive.py [source_file] -d [destination_file] -n [n_value] -t [type] -p
  ```
- **Decoding:**
  ```
  python3 huffman_adaptive.py [source_file] -d [destination_file] -D -p
  ```

### Adaptive Strategies
- **Freeze**: Freezes the Huffman tree after initial construction.
- **Reconstruct**: Rebuilds the Huffman tree periodically.
- **Normalize**: Halves frequencies upon reaching a certain limit to prevent overflow.

### File Handling and Performance
Handles large files efficiently by processing data in chunks. Performance varies based on data distribution and adaptive strategy.
