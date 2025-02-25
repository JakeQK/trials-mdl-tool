import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QVBoxLayout, 
                            QHBoxLayout, QWidget, QPushButton, QLabel, QStatusBar,
                            QComboBox, QAction, QMenu, QMenuBar)
from PyQt5.QtCore import Qt
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtOpenGL import QGLWidget
import tempfile
import shutil

# Import the MDL parser tool
import mdl_tool

class BasicGLWidget(QGLWidget):
    """A simplified OpenGL widget for rendering OBJ models"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vertices = []
        self.faces = []
        self.normals = []
        self.rotation_x = 0
        self.rotation_y = 0
        self.zoom = -10.0
        self.last_pos = None
        
        # Rendering flags
        self.show_wireframe = True
        self.show_solid = True

    def load_obj(self, obj_file):
        """Load vertices and faces from an OBJ file"""
        self.vertices = []
        self.faces = []
        self.normals = []  # Added normals list
        
        print(f"Loading OBJ file: {obj_file}")
        try:
            with open(obj_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if not parts:
                        continue
                        
                    if parts[0] == 'v':
                        # Parse vertex
                        if len(parts) >= 4:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            self.vertices.append((x, y, z))
                            
                    elif parts[0] == 'f':
                        # Parse face (1-based indices in OBJ format)
                        face = []
                        for p in parts[1:4]:  # Get only first 3 vertices for triangles
                            idx = int(p.split('/')[0]) - 1  # OBJ uses 1-based indexing
                            face.append(idx)
                        if len(face) == 3:
                            self.faces.append(face)
                            
            print(f"Loaded {len(self.vertices)} vertices and {len(self.faces)} faces")
            
            # Calculate normals for each face
            self.calculate_normals()
            
            # Calculate the bounds for centering and zooming
            if self.vertices:
                self.center_and_scale()
            
            self.updateGL()
            return True
        except Exception as e:
            print(f"Error loading OBJ: {e}")
            return False
            
    def calculate_normals(self):
        """Calculate normals for all faces"""
        self.normals = []
        
        for face in self.faces:
            if len(face) >= 3:
                # Make sure indices are valid
                if all(idx < len(self.vertices) for idx in face):
                    v0 = self.vertices[face[0]]
                    v1 = self.vertices[face[1]]
                    v2 = self.vertices[face[2]]
                    
                    # Calculate vectors from v0 to v1 and v0 to v2
                    u = [v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]]
                    v = [v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2]]
                    
                    # Calculate normal with cross product
                    normal = [
                        u[1]*v[2] - u[2]*v[1],
                        u[2]*v[0] - u[0]*v[2],
                        u[0]*v[1] - u[1]*v[0]
                    ]
                    
                    # Normalize the vector
                    length = np.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
                    if length > 0:
                        normal = [normal[0]/length, normal[1]/length, normal[2]/length]
                    else:
                        normal = [0, 0, 1]  # Default if calculation fails
                        
                    self.normals.append(normal)
                else:
                    self.normals.append([0, 0, 1])  # Default normal
            
    def center_and_scale(self):
        """Center and scale the model to fit in view"""
        if not self.vertices:
            return
            
        # Find min/max coordinates
        xs = [v[0] for v in self.vertices]
        ys = [v[1] for v in self.vertices]
        zs = [v[2] for v in self.vertices]
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)
        
        # Calculate center
        self.center_x = (min_x + max_x) / 2
        self.center_y = (min_y + max_y) / 2
        self.center_z = (min_z + max_z) / 2
        
        # Calculate dimensions
        width = max_x - min_x
        height = max_y - min_y
        depth = max_z - min_z
        
        # Set zoom based on max dimension
        max_dim = max(width, height, depth)
        if max_dim > 0:
            self.zoom = -max_dim * 2
            print(f"Setting zoom to {self.zoom} based on model size {max_dim}")
        else:
            self.zoom = -10.0
            
    def initializeGL(self):
        """Initialize OpenGL settings"""
        glClearColor(0.2, 0.2, 0.2, 1.0)  # Dark gray background
        glEnable(GL_DEPTH_TEST)
        
        # Enable lighting for better 3D appearance
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        
        # Set light position and properties
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])  # Directional light from top-right
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])   # Ambient light
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])   # Diffuse light
        
        # Enable smooth shading
        glShadeModel(GL_SMOOTH)
        
    def resizeGL(self, width, height):
        """Handle window resize"""
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / height if height > 0 else 1.0
        gluPerspective(45, aspect, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        
    def paintGL(self):
        """Render the scene"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Set up camera
        glTranslatef(0, 0, self.zoom)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        
        # Center the model
        if hasattr(self, 'center_x'):
            glTranslatef(-self.center_x, -self.center_y, -self.center_z)
        
        # Draw coordinate axes (for reference)
        # Disable lighting for axes
        glDisable(GL_LIGHTING)
        glBegin(GL_LINES)
        # X axis - red
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(2, 0, 0)
        # Y axis - green
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 2, 0)
        # Z axis - blue
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 2)
        glEnd()
        
        # Draw model with lighting 
        if self.vertices and self.faces and self.normals:
            # Draw solid model
            if self.show_solid:
                glEnable(GL_LIGHTING)
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                glColor3f(0.75, 0.75, 0.75)  # Light gray color
                
                glBegin(GL_TRIANGLES)
                for i, face in enumerate(self.faces):
                    # Apply the face normal
                    if i < len(self.normals):
                        glNormal3fv(self.normals[i])
                    
                    # Draw the vertices
                    for vertex_idx in face:
                        # Check index is valid
                        if 0 <= vertex_idx < len(self.vertices):
                            glVertex3fv(self.vertices[vertex_idx])
                glEnd()
            
            # Draw wireframe
            if self.show_wireframe:
                glDisable(GL_LIGHTING)
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                glColor3f(0.0, 0.0, 0.0)  # Black wireframe
                glLineWidth(1.0)
                
                glBegin(GL_TRIANGLES)
                for face in self.faces:
                    for vertex_idx in face:
                        if 0 <= vertex_idx < len(self.vertices):
                            glVertex3fv(self.vertices[vertex_idx])
                glEnd()
            
            # Reset to fill mode
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            
    def mousePressEvent(self, event):
        """Handle mouse press for rotation"""
        self.last_pos = event.pos()
        
    def mouseMoveEvent(self, event):
        """Handle mouse drag for rotation"""
        if self.last_pos:
            dx = event.x() - self.last_pos.x()
            dy = event.y() - self.last_pos.y()
            
            if event.buttons() & Qt.LeftButton:
                self.rotation_y += dx
                self.rotation_x += dy
                self.updateGL()
                
            self.last_pos = event.pos()
            
    def wheelEvent(self, event):
        """Handle mouse wheel for zoom"""
        delta = event.angleDelta().y() / 120
        self.zoom += delta * 0.5
        self.updateGL()


class BasicMDLViewer(QMainWindow):
    """A simplified MDL viewer application"""
    def __init__(self):
        super().__init__()
        self.temp_dir = tempfile.mkdtemp()
        self.obj_file = None
        self.mdl_file = None
        self.lod_count = 0
        self.current_lod = 0
        
        # Initialize UI
        self.init_ui()
        
        # Connect signals after UI is initialized
        self.lod_combo.currentIndexChanged.connect(self.change_lod)
        
    def init_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("MDL Viewer")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create top control panel
        control_layout = QHBoxLayout()
        
        # File operations panel
        file_group = QWidget()
        file_layout = QVBoxLayout(file_group)
        file_layout.setContentsMargins(5, 5, 5, 5)
        
        # Title for file panel
        file_title = QLabel("<b>File Operations</b>")
        file_layout.addWidget(file_title)
        
        # Add button to open MDL files
        self.open_button = QPushButton("Open MDL File", self)
        self.open_button.clicked.connect(self.open_mdl_file)
        file_layout.addWidget(self.open_button)
        
        # Add button to export OBJ
        self.export_button = QPushButton("Export OBJ File", self)
        self.export_button.clicked.connect(self.export_obj_file)
        self.export_button.setEnabled(False)  # Initially disabled
        file_layout.addWidget(self.export_button)
        
        control_layout.addWidget(file_group)
        
        # LOD selection panel
        lod_group = QWidget()
        lod_layout = QVBoxLayout(lod_group)
        lod_layout.setContentsMargins(5, 5, 5, 5)
        
        # Title for LOD panel
        lod_title = QLabel("<b>LOD Selection</b>")
        lod_layout.addWidget(lod_title)
        
        # LOD selector
        lod_selector_layout = QHBoxLayout()
        self.lod_label = QLabel("LOD Level:")
        self.lod_combo = QComboBox()
        # Signal connection is now in __init__
        self.lod_combo.setEnabled(False)  # Initially disabled
        
        lod_selector_layout.addWidget(self.lod_label)
        lod_selector_layout.addWidget(self.lod_combo)
        lod_layout.addLayout(lod_selector_layout)
        
        # Add information about current LOD
        self.lod_info = QLabel("No model loaded")
        lod_layout.addWidget(self.lod_info)
        
        control_layout.addWidget(lod_group)
        
        # Rendering options panel
        render_group = QWidget()
        render_layout = QVBoxLayout(render_group)
        render_layout.setContentsMargins(5, 5, 5, 5)
        
        # Title for rendering panel
        render_title = QLabel("<b>Rendering Options</b>")
        render_layout.addWidget(render_title)
        
        # Add wireframe toggle
        self.wireframe_button = QPushButton("Wireframe", self)
        self.wireframe_button.setCheckable(True)
        self.wireframe_button.setChecked(True)
        self.wireframe_button.clicked.connect(self.toggle_wireframe)
        render_layout.addWidget(self.wireframe_button)
        
        # Add solid toggle  
        self.solid_button = QPushButton("Solid", self)
        self.solid_button.setCheckable(True)
        self.solid_button.setChecked(True)
        self.solid_button.clicked.connect(self.toggle_solid)
        render_layout.addWidget(self.solid_button)
        
        # Add reset view button
        self.reset_view_button = QPushButton("Reset View", self)
        self.reset_view_button.clicked.connect(self.reset_view)
        render_layout.addWidget(self.reset_view_button)
        
        control_layout.addWidget(render_group)
        
        # Add control layout to main layout
        main_layout.addLayout(control_layout, 1)  # Small height proportion
        
        # Create OpenGL widget
        self.gl_widget = BasicGLWidget(self)
        main_layout.addWidget(self.gl_widget, 10)  # Large height proportion
        
        # Add status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create menu bar
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        open_action = QAction("Open MDL File", self)
        open_action.triggered.connect(self.open_mdl_file)
        file_menu.addAction(open_action)
        
        export_action = QAction("Export OBJ File", self)
        export_action.triggered.connect(self.export_obj_file)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("View")
        
        wireframe_action = QAction("Toggle Wireframe", self)
        wireframe_action.setCheckable(True)
        wireframe_action.setChecked(True)
        wireframe_action.triggered.connect(self.toggle_wireframe)
        view_menu.addAction(wireframe_action)
        
        solid_action = QAction("Toggle Solid", self)
        solid_action.setCheckable(True)
        solid_action.setChecked(True)
        solid_action.triggered.connect(self.toggle_solid)
        view_menu.addAction(solid_action)
        
        view_menu.addSeparator()
        
        reset_action = QAction("Reset View", self)
        reset_action.triggered.connect(self.reset_view)
        view_menu.addAction(reset_action)
        
    def toggle_wireframe(self, checked):
        """Toggle wireframe rendering"""
        self.gl_widget.show_wireframe = checked
        self.gl_widget.updateGL()
        
    def toggle_solid(self, checked):
        """Toggle solid rendering"""
        self.gl_widget.show_solid = checked
        self.gl_widget.updateGL()
        
    def reset_view(self):
        """Reset the view to center the model"""
        if hasattr(self.gl_widget, 'center_and_scale'):
            self.gl_widget.rotation_x = 0
            self.gl_widget.rotation_y = 0
            self.gl_widget.center_and_scale()
            self.gl_widget.updateGL()
            
    def open_mdl_file(self):
        """Open and process an MDL file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open MDL File", "", "MDL Files (*.mdl);;All Files (*)"
        )
        
        if not file_path:
            return
            
        self.mdl_file = file_path
        self.status_bar.showMessage(f"Loading {os.path.basename(file_path)}...")
        
        try:
            # Read MDL header to get LOD count
            with open(file_path, 'rb') as f:
                header = mdl_tool.parse_header(f)
                self.lod_count = header['lod_count']
                print(f"MDL file has {self.lod_count} LODs")
                
            # Update UI
            self.lod_combo.clear()
            # Temporarily disconnect signal to avoid triggering change_lod during setup
            self.lod_combo.blockSignals(True)
            for i in range(self.lod_count):
                self.lod_combo.addItem(f"LOD {i}")
            
            # Enable controls
            self.lod_combo.setEnabled(True)
            self.export_button.setEnabled(True)
            
            # Default to first LOD
            if self.lod_count > 0:
                self.current_lod = 0
                self.lod_combo.setCurrentIndex(0)
                # Re-enable signals before loading
                self.lod_combo.blockSignals(False)
                # Load the LOD directly
                self.load_lod(0)
            else:
                self.lod_info.setText("Model has no LODs")
                self.lod_combo.blockSignals(False)
                
        except Exception as e:
            self.status_bar.showMessage(f"Error loading MDL: {str(e)}")
            print(f"Error loading MDL: {e}")
            if self.lod_combo.signalsBlocked():
                self.lod_combo.blockSignals(False)
            
    def change_lod(self, index):
        """Handle LOD selection change"""
        print(f"LOD selection changed to index {index}")  # Debug print
        if index >= 0 and index < self.lod_count:
            self.current_lod = index
            self.load_lod(index)
            print(f"Loading LOD {index}")  # Debug print
        else:
            print(f"Invalid LOD index: {index}, lod_count: {self.lod_count}")  # Debug print
            
    def load_lod(self, lod_index):
        """Load the specified LOD"""
        if not self.mdl_file:
            return
            
        self.status_bar.showMessage(f"Loading LOD {lod_index}...")
        
        try:
            # Create temp directory for extraction
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)
            
            # Use mdl_tool to extract the specified LOD
            mdl_tool.parse_mdl_file(
                self.mdl_file,
                output_dir=self.temp_dir,
                lod_indices=[lod_index],
                skip_binary=True,
                verbose=True
            )
            
            # Find and load the OBJ file
            obj_file = os.path.join(self.temp_dir, f"lod_{lod_index}.obj")
            if os.path.exists(obj_file):
                self.obj_file = obj_file
                if self.gl_widget.load_obj(obj_file):
                    self.status_bar.showMessage(f"Loaded LOD {lod_index} from {os.path.basename(self.mdl_file)}")
                    
                    # Update info
                    vertex_count = len(self.gl_widget.vertices)
                    face_count = len(self.gl_widget.faces)
                    self.lod_info.setText(f"LOD {lod_index}: {vertex_count} vertices, {face_count} faces")
                else:
                    self.status_bar.showMessage("Failed to load the extracted model")
            else:
                self.status_bar.showMessage("Failed to extract OBJ from MDL file")
                
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
            print(f"Error processing MDL: {e}")
            
    def export_obj_file(self):
        """Export the current OBJ file"""
        if not self.obj_file or not os.path.exists(self.obj_file):
            self.status_bar.showMessage("No model loaded to export")
            return
            
        # Get export path from user
        mdl_basename = os.path.splitext(os.path.basename(self.mdl_file))[0] if self.mdl_file else "model"
        suggested_name = f"{mdl_basename}_lod{self.current_lod}.obj"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export OBJ File", suggested_name, "OBJ Files (*.obj);;All Files (*)"
        )
        
        if not file_path:
            return
            
        try:
            # Copy the OBJ file to the selected location
            shutil.copy2(self.obj_file, file_path)
            self.status_bar.showMessage(f"Exported OBJ to {file_path}")
        except Exception as e:
            self.status_bar.showMessage(f"Error exporting OBJ: {str(e)}")
            print(f"Error exporting OBJ: {e}")
    
    def closeEvent(self, event):
        """Clean up temp files when closing"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except:
            pass
        event.accept()


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    viewer = BasicMDLViewer()
    viewer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()