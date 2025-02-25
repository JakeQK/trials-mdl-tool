import struct
import os
import zlib

def parse_mdl_file(filepath):
    """
    Parse the Trials Fusion .mdl file format and output an OBJ for each LOD.
    
    Args:
        filepath: Path to the .mdl file
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
                exit()
            
            try:
                decompressed_face_data = zlib.decompress(compressed_face_data)
            except zlib.error as e:
                print(f"  Error decompressing face data: {e}")
                exit()
            
            # Process decompressed_geometry_data to extract vertices
            vertices = []
            geometry_data = decompressed_geometry_data

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
            
            print(f"  Extracted {len(vertices)} vertices from geometry data")
            
            # Process decompressed_face_data to extract faces
            faces = []
            face_data = decompressed_face_data
            
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
            
            print(f"  Extracted {len(faces)} faces from face data")
            
            # Write to OBJ file
            obj_filename = f"extracted_lod_data/lod_{lod_index}.obj"
            
            with open(obj_filename, 'w') as obj_file:
                obj_file.write(f"# OBJ file - LOD {lod_index}\n")
                obj_file.write(f"# Vertices: {len(vertices)}\n")
                obj_file.write(f"# Faces: {len(faces)}\n\n")
                
                # Write vertices with higher precision
                for i, (x, y, z) in enumerate(vertices):
                    obj_file.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
                
                # Write faces
                for v1, v2, v3 in faces:
                    obj_file.write(f"f {v1} {v2} {v3}\n")
            
            print(f"  Saved OBJ file to {obj_filename}")
            
            # Also save the raw decompressed data for reference
            combined_data = decompressed_geometry_data + decompressed_face_data
            binary_filename = f"extracted_lod_data/lod_{lod_index}_decompressed.bin"
            
            with open(binary_filename, 'wb') as bin_file:
                bin_file.write(combined_data)
            
            print(f"  Saved raw decompressed data to {binary_filename}")
            print(f"  Total decompressed size: {len(combined_data)} bytes")
            print(f"  (Geometry: {len(decompressed_geometry_data)} bytes, Face: {len(decompressed_face_data)} bytes)")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python mdl_tool.py <mdl_file_path>")
        sys.exit(1)
    
    model_file_path = sys.argv[1]
    parse_mdl_file(model_file_path)
    print("\nProcessing complete!")