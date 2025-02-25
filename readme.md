# MDL Viewer

A 3D model viewer application specifically designed to load, convert, and render Trials Fusion MDL model files. The application integrates with `mdl_tool.py` to convert MDL files to OBJ format and then renders them using OpenGL.

## Features

- File browser to select MDL files
- Automatic conversion of MDL to OBJ format using mdl_tool.py
- Support for viewing different LOD (Level of Detail) models
- Interactive 3D viewer with rotation and zoom controls
- Toggle between solid and wireframe rendering modes
- Reset view option to recenter the model

## Requirements

- Python 3.6 or higher
- PyQt5
- PyOpenGL
- NumPy

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
python mdl_viewer.py
```

2. Click on "Open MDL" from the menu or toolbar
3. Navigate to and select a .mdl file
4. The application will automatically convert and display the first LOD of the model
5. Use the LOD dropdown to switch between different Level of Detail models
6. Controls:
   - Left-click and drag to rotate the model
   - Scroll wheel to zoom in/out
   - Use the "Wireframe" and "Solid" buttons to toggle different display modes
   - Click "Reset View" to recenter the model

## How It Works

1. The application uses your `mdl_tool.py` module to convert MDL files to OBJ format
2. Conversion is performed in a background thread to keep the UI responsive
3. The converted OBJ file is loaded into an OpenGL renderer for display
4. Face normals are calculated for proper lighting if not present in the OBJ file

## System Requirements

- Graphics card with OpenGL support
- Sufficient RAM to load large 3D models

## Troubleshooting

- If models appear too large or small, try clicking "Reset View"
- If no model appears after loading a file, check the console for error messages
- For large models, the conversion and loading process may take a few moments

## License

This project is provided as-is for personal use.
