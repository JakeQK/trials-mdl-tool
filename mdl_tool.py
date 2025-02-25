import struct
import os
import zlib

def parse_model_file(filepath):
    """
    Parse the 3D model file format and extract compressed geometry and face data for each LOD.
    
    Args:
        filepath: Path to the model file
    """
    with open(filepath, 'rb') as f:
        # Parse header
        signature = f.read(3)
        marker1 = f.read(1)
        version = f.read(5)
        unknown1 = struct.unpack('i', f.read(4))[0]
        marker2 = f.read(1)
        lrs01 = f.read(5)
        lod_count = struct.unpack('i', f.read(4))[0]
        
        print(f"File Header:")
        print(f"  Signature: {signature}")
        print(f"  Marker: {marker1.hex()}")
        print(f"  Version: {version}")
        print(f"  Unknown value: {unknown1}")
        print(f"  Marker: {marker2.hex()}")
        print(f"  LRS01: {lrs01}")
        print(f"  LOD Count: {lod_count}")
        
        # Verify signature
        if signature != b'OBJ':
            print(f"Warning: Unexpected file signature: {signature}, expected: b'OBJ'")

        
        # Create output directory if it doesn't exist
        os.makedirs("extracted_lod_data", exist_ok=True)
        
        # Process each LOD
        for lod_index in range(lod_count):
            print(f"\nProcessing LOD {lod_index}:")
            
            # Read LOD marker and identifier
            lod_marker = f.read(1)
            lr005 = f.read(5)
            
            # Read unknown vector3
            unknown_vec3 = struct.unpack('fff', f.read(12))
            
            # Read string
            string_length = struct.unpack('i', f.read(4))[0]
            string_data = f.read(string_length)
            
            # Read unknown data block
            unknown_data1 = f.read(56)
            
            # Read ID string
            id_string_length = struct.unpack('h', f.read(2))[0]
            id_string = f.read(id_string_length)
            
            # Read another unknown data block
            unknown_data2 = f.read(10)
            
            # Read compressed geometry data
            compressed_geometry_data_len = struct.unpack('i', f.read(4))[0]
            compressed_geometry_data = f.read(compressed_geometry_data_len)
            
            # Read unknown value
            unknown2 = struct.unpack('i', f.read(4))[0]
            
            # Read compressed face data
            compressed_face_data_len = struct.unpack('i', f.read(4))[0]
            compressed_face_data = f.read(compressed_face_data_len)
            
            print(f"  Marker: {lod_marker.hex()}")
            print(f"  LR005: {lr005}")
            print(f"  Unknown vector3: {unknown_vec3}")
            print(f"  String length: {string_length}")
            print(f"  String: {string_data}")
            print(f"  ID string length: {id_string_length}")
            print(f"  ID string: {id_string}")
            print(f"  Compressed geometry data length: {compressed_geometry_data_len}")
            print(f"  Unknown value: {unknown2}")
            print(f"  Compressed face data length: {compressed_face_data_len}")
            
            # Decompress the data
            try:
                decompressed_geometry_data = zlib.decompress(compressed_geometry_data)
                print(f"  Decompressed geometry data size: {len(decompressed_geometry_data)} bytes")
            except zlib.error as e:
                print(f"  Error decompressing geometry data: {e}")
                decompressed_geometry_data = compressed_geometry_data
                print(f"  Using compressed geometry data instead: {len(decompressed_geometry_data)} bytes")
            
            try:
                decompressed_face_data = zlib.decompress(compressed_face_data)
                print(f"  Decompressed face data size: {len(decompressed_face_data)} bytes")
            except zlib.error as e:
                print(f"  Error decompressing face data: {e}")
                decompressed_face_data = compressed_face_data
                print(f"  Using compressed face data instead: {len(decompressed_face_data)} bytes")
            
            # Concatenate the decompressed data and save to file
            combined_data = decompressed_geometry_data + decompressed_face_data
            output_filename = f"extracted_lod_data/lod_{lod_index}_decompressed.bin"
            
            with open(output_filename, 'wb') as out_file:
                out_file.write(combined_data)
            
            print(f"  Saved combined decompressed data to {output_filename}")
            print(f"  Total decompressed size: {len(combined_data)} bytes")
            print(f"  (Geometry: {len(decompressed_geometry_data)} bytes, Face: {len(decompressed_face_data)} bytes)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python model_parser.py <model_file_path>")
        sys.exit(1)
    
    model_file_path = sys.argv[1]
    parse_model_file(model_file_path)
    print("\nProcessing complete!")