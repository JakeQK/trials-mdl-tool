import struct
import os
import zlib
import argparse
import logging
from typing import Tuple, List, BinaryIO, Optional, Dict, Any

# Constants for file format
OBJ_SIGNATURE = b'OBJ'
LRS01_MARKER = b'LRS01'
LR005_MARKER = b'LR005'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class MDLParseError(Exception):
    """Exception raised for errors in parsing MDL files."""
    pass

def parse_mdl_file(filepath: str, output_dir: str = "extracted_lod_data", 
                   lod_indices: Optional[List[int]] = None, 
                   skip_binary: bool = False,
                   verbose: bool = False) -> None:
    """
    Parse the Trials Fusion .mdl file format and output an OBJ for each LOD.
    
    Args:
        filepath: Path to the .mdl file
        output_dir: Directory to save extracted files (default: "extracted_lod_data")
        lod_indices: Specific LOD indices to extract (default: None, extract all)
        skip_binary: Skip saving raw binary data (default: False)
        verbose: Enable verbose output (default: False)
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
    
    try:
        with open(filepath, 'rb') as f:
            # Parse header
            header = parse_header(f)
            log_header_info(header)
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Determine which LODs to process
            lod_count = header['lod_count']
            if lod_indices is None:
                lod_indices = list(range(lod_count))
            else:
                # Filter out invalid indices
                lod_indices = [i for i in lod_indices if 0 <= i < lod_count]
                if not lod_indices:
                    raise MDLParseError(f"No valid LOD indices specified. File has {lod_count} LODs (0-{lod_count-1}).")
            
            # Process each requested LOD
            for i, lod_index in enumerate(lod_indices):
                logger.info(f"Processing LOD {lod_index} ({i+1}/{len(lod_indices)})...")
                process_lod(f, lod_index, output_dir, skip_binary)
                
        logger.info("Processing complete!")
        
    except FileNotFoundError:
        logger.error(f"File '{filepath}' not found.")
        raise
    except IOError as e:
        logger.error(f"I/O error occurred: {e}")
        raise
    except MDLParseError as e:
        logger.error(f"MDL parsing error: {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise

def parse_header(f: BinaryIO) -> Dict[str, Any]:
    """
    Parse the MDL file header.
    
    Args:
        f: Open file handle positioned at the start of the header
        
    Returns:
        Dictionary containing header information
    """
    header = {}
    header['signature'] = f.read(3)
    header['marker1'] = f.read(1)
    header['version'] = f.read(5)
    header['unknown1'] = struct.unpack('i', f.read(4))[0]
    header['marker2'] = f.read(1)
    header['lrs01'] = f.read(5)
    header['lod_count'] = struct.unpack('i', f.read(4))[0]
    
    # Verify signature
    if header['signature'] != OBJ_SIGNATURE:
        logger.warning(f"Unexpected file signature: {header['signature']}, expected: {OBJ_SIGNATURE}")
    
    return header

def log_header_info(header: Dict[str, Any]) -> None:
    """
    Log information about the file header.
    
    Args:
        header: Dictionary containing header information
    """
    logger.info("File Header:")
    logger.info(f"  Signature: {header['signature']}")
    logger.info(f"  Marker: {header['marker1'].hex()}")
    logger.info(f"  Version: {header['version']}")
    logger.info(f"  Unknown value: {header['unknown1']}")
    logger.info(f"  Marker: {header['marker2'].hex()}")
    logger.info(f"  LRS01: {header['lrs01']}")
    logger.info(f"  LOD Count: {header['lod_count']}")

def process_lod(f: BinaryIO, lod_index: int, output_dir: str, skip_binary: bool) -> None:
    """
    Process a single LOD from the MDL file.
    
    Args:
        f: Open file handle positioned at the start of the LOD
        lod_index: Index of the LOD being processed
        output_dir: Directory to save extracted files
        skip_binary: Skip saving raw binary data
    """
    # Read LOD header
    lod_data = read_lod_header(f)
    log_lod_header_info(lod_data)
    
    try:
        # Decompress geometry data
        decompressed_geometry_data = decompress_data(
            lod_data['compressed_geometry_data'], 
            "geometry"
        )
        
        # Decompress face data
        decompressed_face_data = decompress_data(
            lod_data['compressed_face_data'], 
            "face"
        )
        
        # Extract vertices and faces
        vertices = extract_vertices(decompressed_geometry_data)
        faces = extract_faces(decompressed_face_data)
        
        logger.info(f"  Extracted {len(vertices)} vertices from geometry data")
        logger.info(f"  Extracted {len(faces)} faces from face data")
        
        # Save to OBJ file
        obj_filename = os.path.join(output_dir, f"lod_{lod_index}.obj")
        save_obj_file(obj_filename, vertices, faces, lod_index)
        logger.info(f"  Saved OBJ file to {obj_filename}")
        
        # Save raw decompressed data for reference if requested
        if not skip_binary:
            save_binary_data(output_dir, lod_index, decompressed_geometry_data, decompressed_face_data)
    
    except zlib.error as e:
        logger.error(f"  Error processing LOD {lod_index}: {e}")
        raise MDLParseError(f"Failed to decompress data for LOD {lod_index}: {e}")

def read_lod_header(f: BinaryIO) -> Dict[str, Any]:
    """
    Read the header for a single LOD.
    
    Args:
        f: Open file handle positioned at the start of the LOD
        
    Returns:
        Dictionary containing LOD header information
    """
    lod_data = {}
    
    # Read LOD marker and identifier
    lod_data['lod_marker'] = f.read(1)
    lod_data['lr005'] = f.read(5)
    
    # Read unknown vector3
    lod_data['unknown_vec3'] = struct.unpack('fff', f.read(12))
    
    # Read string
    string_length = struct.unpack('i', f.read(4))[0]
    lod_data['string_length'] = string_length
    lod_data['string_data'] = f.read(string_length)
    
    # Read unknown data block
    lod_data['unknown_data1'] = f.read(56)
    
    # Read ID string
    id_string_length = struct.unpack('h', f.read(2))[0]
    lod_data['id_string_length'] = id_string_length
    lod_data['id_string'] = f.read(id_string_length)
    
    # Read another unknown data block
    lod_data['unknown_data2'] = f.read(7)

    # Read unknown 4 byte value count, it tells us how many 4 byte values follow after this+2 bytes
    four_byte_value_count = struct.unpack('b', f.read(1))[0]
    lod_data['four_byte_value_count'] = four_byte_value_count

    # NOTE
    # Majority of objects, the four_byte_value_count is 0, this was considered normal
    # Some objects, such as rider customization, seem to have a value, and even when addressing/ignoring the extra bytes
    # The object doesn't seem to load correctly, so I will need to investigate why the object model isn't being read correctly when these values are present

    # Read another unknown data block, consisting of a number of 4 byte values and 2 bytes
    lod_data['unknown_data3'] = f.read(four_byte_value_count * 4 + 2)
    
    # Read compressed geometry data
    compressed_geometry_data_len = struct.unpack('i', f.read(4))[0]
    lod_data['compressed_geometry_data_len'] = compressed_geometry_data_len
    lod_data['compressed_geometry_data'] = f.read(compressed_geometry_data_len)
    
    # Read unknown value
    lod_data['unknown2'] = struct.unpack('i', f.read(4))[0]
    
    # Read compressed face data
    compressed_face_data_len = struct.unpack('i', f.read(4))[0]
    lod_data['compressed_face_data_len'] = compressed_face_data_len
    lod_data['compressed_face_data'] = f.read(compressed_face_data_len)
    
    return lod_data

def log_lod_header_info(lod_data: Dict[str, Any]) -> None:
    """
    Log information about a LOD header.
    
    Args:
        lod_data: Dictionary containing LOD data
    """
    logger.debug(f"  Marker: {lod_data['lod_marker'].hex()}")
    logger.debug(f"  LR005: {lod_data['lr005']}")
    logger.debug(f"  Unknown vector3: {lod_data['unknown_vec3']}")
    logger.debug(f"  String length: {lod_data['string_length']}")
    logger.debug(f"  String: {lod_data['string_data']}")
    logger.debug(f"  ID string length: {lod_data['id_string_length']}")
    logger.debug(f"  ID string: {lod_data['id_string']}")
    logger.debug(f"  Compressed geometry data length: {lod_data['compressed_geometry_data_len']}")
    logger.debug(f"  Unknown value: {lod_data['unknown2']}")
    logger.debug(f"  Compressed face data length: {lod_data['compressed_face_data_len']}")

def decompress_data(compressed_data: bytes, data_type: str) -> bytes:
    """
    Decompress zlib-compressed data.
    
    Args:
        compressed_data: Compressed data bytes
        data_type: Type of data being decompressed (for logging)
        
    Returns:
        Decompressed data bytes
    """
    try:
        decompressed_data = zlib.decompress(compressed_data)
        logger.debug(f"  Decompressed {data_type} data size: {len(decompressed_data)} bytes")
        return decompressed_data
    except zlib.error as e:
        logger.error(f"  Error decompressing {data_type} data: {e}")
        raise

def extract_vertices(geometry_data: bytes) -> List[Tuple[float, float, float]]:
    """
    Extract vertices from decompressed geometry data.
    
    Args:
        geometry_data: Decompressed geometry data bytes
        
    Returns:
        List of vertex coordinates (x, y, z)
    """
    vertices = []
    
    # Skip the first 4 bytes of unknown data
    offset = 4
    
    # Each vertex is 6 bytes (three 2-byte floats) followed by 10 bytes of unknown data
    vertex_size = 4 + 6 + 10
    
    while offset + vertex_size <= len(geometry_data) + 4:
        # Extract the raw bytes for vertex coordinates
        x_bytes = geometry_data[offset:offset+2]
        y_bytes = geometry_data[offset+2:offset+4]
        z_bytes = geometry_data[offset+4:offset+6]
        
        # Convert to signed 16-bit integers (little-endian)
        x_int = struct.unpack('<h', x_bytes)[0]
        y_int = struct.unpack('<h', y_bytes)[0]
        z_int = struct.unpack('<h', z_bytes)[0]
        
        # Convert to float by dividing by 256.0
        x = x_int / 256.0
        y = y_int / 256.0
        z = z_int / 256.0
        
        vertices.append((x, y, z))
        
        # Skip to the next vertex
        offset += vertex_size
    
    return vertices

def extract_faces(face_data: bytes) -> List[Tuple[int, int, int]]:
    """
    Extract faces from decompressed face data.
    
    Args:
        face_data: Decompressed face data bytes
        
    Returns:
        List of face vertex indices (v1, v2, v3)
    """
    faces = []
    
    # Each face is 3 shorts (2 bytes each) representing vertex indices
    face_size = 2 * 3
    offset = 0
    
    while offset + face_size <= len(face_data):
        v1 = struct.unpack('h', face_data[offset:offset+2])[0]
        v2 = struct.unpack('h', face_data[offset+2:offset+4])[0]
        v3 = struct.unpack('h', face_data[offset+4:offset+6])[0]
        
        # OBJ format uses 1-based indices
        faces.append((v1 + 1, v2 + 1, v3 + 1))
        
        # Skip to the next face
        offset += face_size
    
    return faces

def save_obj_file(filename: str, vertices: List[Tuple[float, float, float]], 
                  faces: List[Tuple[int, int, int]], lod_index: int) -> None:
    """
    Save vertices and faces to an OBJ file.
    
    Args:
        filename: Path to save the OBJ file
        vertices: List of vertex coordinates
        faces: List of face vertex indices
        lod_index: Index of the LOD being saved
    """
    with open(filename, 'w') as obj_file:
        obj_file.write(f"# OBJ file - LOD {lod_index}\n")
        obj_file.write(f"# Vertices: {len(vertices)}\n")
        obj_file.write(f"# Faces: {len(faces)}\n\n")
        
        # Write vertices with higher precision
        for x, y, z in vertices:
            obj_file.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
        
        # Write faces
        for v1, v2, v3 in faces:
            obj_file.write(f"f {v1} {v2} {v3}\n")

def save_binary_data(output_dir: str, lod_index: int, 
                     geometry_data: bytes, face_data: bytes) -> None:
    """
    Save raw decompressed data for reference.
    
    Args:
        output_dir: Directory to save the binary file
        lod_index: Index of the LOD being saved
        geometry_data: Decompressed geometry data bytes
        face_data: Decompressed face data bytes
    """
    combined_data = geometry_data + face_data
    binary_filename = os.path.join(output_dir, f"lod_{lod_index}_decompressed.bin")
    
    with open(binary_filename, 'wb') as bin_file:
        bin_file.write(combined_data)
    
    logger.info(f"  Saved raw decompressed data to {binary_filename}")
    logger.info(f"  Total decompressed size: {len(combined_data)} bytes")
    logger.info(f"  (Geometry: {len(geometry_data)} bytes, Face: {len(face_data)} bytes)")

def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description='Parse Trials Fusion .mdl files and extract 3D models.'
    )
    
    parser.add_argument(
        'mdl_file',
        help='Path to the .mdl file to parse'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='extracted_lod_data',
        help='Directory to save extracted files (default: "extracted_lod_data")'
    )
    
    parser.add_argument(
        '-l', '--lod',
        type=int,
        action='append',
        help='Specific LOD index to extract (can be used multiple times)'
    )
    
    parser.add_argument(
        '-s', '--skip-binary',
        action='store_true',
        help='Skip saving raw binary data'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        parse_mdl_file(
            args.mdl_file,
            output_dir=args.output_dir,
            lod_indices=args.lod,
            skip_binary=args.skip_binary,
            verbose=args.verbose
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()