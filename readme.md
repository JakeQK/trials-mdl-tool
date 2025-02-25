# Trials MDL Extractor & Viewer

A Python-based tool for extracting and viewing 3D models from RedLynx's Trials game series. This application allows you to extract and convert the proprietary `.mdl` format used in Trials games to the standard OBJ format, as well as interactively view the 3D models.

![Trials MDL Viewer](https://github.com/user-attachments/assets/6753d292-4bd6-420b-85f4-424adc45c2fc)

## Features

- Extract 3D models from Trials `.mdl` files
- Interactive 3D viewer with multiple rendering options
- Support for multiple LOD (Level of Detail) models
- Export extracted models to standard OBJ format
- Wireframe and solid shading view options
- Model information display (vertex/face count)

## Requirements

- Python 3.6+
- PyQt5
- PyOpenGL
- NumPy
- zlib (included with Python)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/trials-mdl-viewer.git
   cd trials-mdl-viewer
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

Run the viewer application:
```
python mdl_viewer.py
```

### Using the Viewer

1. Click "Open MDL File" and select a `.mdl` file from your Trials game files
2. The model will be automatically extracted and displayed in the viewer
3. Use the LOD dropdown to switch between different levels of detail
4. Toggle rendering options (Wireframe/Solid) using the buttons on the right
5. Use the mouse to interact with the model:
   - Left-click and drag to rotate
   - Mouse wheel to zoom in/out
6. Click "Reset View" to return to the default view
7. Click "Export OBJ File" to save the current model as an OBJ file

### Command Line Extraction

You can also use the extraction tool directly from the command line:
```
python mdl_tool.py path/to/model.mdl [options]
```

Options:
- `-o, --output-dir`: Directory to save extracted files (default: "extracted_lod_data")
- `-l, --lod`: Specific LOD index to extract (can be used multiple times)
- `-s, --skip-binary`: Skip saving raw binary data
- `-v, --verbose`: Enable verbose output

Example:
```
python mdl_tool.py track_model.mdl -o exported_models -l 0 -l 1 -v
```

## File Format

The Trials `.mdl` format contains compressed 3D model data with the following structure:
- File header with signature and LOD count
- For each LOD:
  - LOD header with metadata
  - zlib-compressed geometry data (vertices)
  - zlib-compressed face data
  
The tool decompresses this data and converts it to the standard OBJ format, which can be used in most 3D modeling applications.

## Game Support

This tool has currently only been tested with models from:
- Trials Fusion

Support for other games in the Trials series (Evolution, Rising, etc.) is planned for future updates but has not been implemented or tested yet.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The RedLynx team for creating the Trials series
- Original research and reverse engineering of the .mdl file format was done solely by the author of this tool

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
