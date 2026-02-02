"""File utilities for compression and data handling.

This module provides functions for writing compressed data to files,
calculating file sizes, and saving model checkpoints.
"""

import pickle
import struct
from pathlib import Path


def write_uints(fd, values, fmt=">{:d}I"):
    """Write unsigned integers to file.
    
    Args:
        fd: File descriptor
        values: List of integer values to write
        fmt: Format string for struct.pack
        
    Returns:
        int: Number of bytes written (4 bytes per number)
    """
    fd.write(struct.pack(fmt.format(len(values)), *values))
    return len(values) * 4

def write_uchars(fd, values, fmt=">{:d}B"):
    """Write unsigned chars to file.
    
    Args:
        fd: File descriptor
        values: List of char values to write
        fmt: Format string for struct.pack
        
    Returns:
        int: Number of bytes written (1 byte per char)
    """
    fd.write(struct.pack(fmt.format(len(values)), *values))
    return len(values) * 1


def write_body(fd, shape, out_strings):
    """Write the main content of the compressed file.
    
    Args:
        fd: File descriptor
        shape: Shape tuple
        out_strings: List of output strings
        
    Returns:
        int: Total number of bytes written
    """
    bytes_cnt = 0
    # Write dimensions and number of strings
    bytes_cnt = write_uints(fd, (shape[0], shape[1], len(out_strings)))
    # Write each data string
    for s in out_strings:
        bytes_cnt += write_uints(fd, (len(s[0]),))
        bytes_cnt += write_bytes(fd, s[0])
    return bytes_cnt


def filesize(filepath: str) -> int:
    """Get file size in bytes.
    
    Args:
        filepath: Path to the file
        
    Returns:
        int: File size in bytes
        
    Raises:
        ValueError: If file path is invalid
    """
    if not Path(filepath).is_file():
        raise ValueError(f'Invalid file "{filepath}".')
    return Path(filepath).stat().st_size

def write_bytes(fd, values, fmt=">{:d}s"):
    """Write byte data to file.
    
    Args:
        fd: File descriptor
        values: Byte values to write
        fmt: Format string for struct.pack
        
    Returns:
        int: Number of bytes written
    """
    if len(values) == 0:
        return
    fd.write(struct.pack(fmt.format(len(values)), values))
    return len(values) * 1

def savecompressed(compressfile, outnet, bitdepth, h, w):
    """Save compressed image to file.
    
    Args:
        compressfile: Path to compressed file
        outnet: Network output dictionary
        bitdepth: Bit depth of the image
        h: Image height
        w: Image width
        
    Returns:
        float: Bits per pixel
    """
    shape = outnet["shape"]
    with Path(compressfile).open("wb") as f:
        write_uints(f, (h, w))  # Write dimensions
        write_uchars(f, (bitdepth,))  # Write bit depth
        write_body(f, shape, outnet["strings"])  # Write compressed data
    size = filesize(compressfile)
    bpp = float(size) * 8 / (h * w)  # Calculate bits per pixel
    return bpp

def save_checkpoint(state, filename="checkpoint.pkl"):
    """Save model state to file.
    
    Args:
        state: Model state dictionary
        filename: Path to checkpoint file
    """
    with open(filename, "wb") as f:
        pickle.dump(state, f)