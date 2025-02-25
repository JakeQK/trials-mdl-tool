import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QVBoxLayout, 
                            QWidget, QPushButton, QLabel, QStatusBar)
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
        self.rotation_x = 0
        self.rotation_y = 0
        self.zoom = -10.0
        self.last_pos = None

    def load_obj(self, obj_file):
        """Load vertices and faces from an OBJ file"""
        self.vertices = []
        self.faces = []
        
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
            
            # Calculate the bounds for centering and zooming
            if self.vertices:
                self.center_and_scale()
            
            self.updateGL()
            return True
        except Exception as e:
            print(f"Error loading OBJ: {e}")
            return False
            
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
        
        # Draw model as wireframe
        if self.vertices and self.faces:
            glColor3f(1.0, 1.0, 1.0)  # White wireframe
            glBegin(GL_TRIANGLES)
            for face in self.faces:
                for vertex_idx in face:
                    # Check index is valid
                    if 0 <= vertex_idx < len(self.vertices):
                        glVertex3fv(self.vertices[vertex_idx])
            glEnd()
            
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
        self.init_ui()
        
    def init_ui(self):
        """Set up the user interface"""
        self.setWindowTitle("Basic MDL Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create OpenGL widget
        self.gl_widget = BasicGLWidget(self)
        layout.addWidget(self.gl_widget)
        
        # Add button to open MDL files
        self.open_button = QPushButton("Open MDL File", self)
        self.open_button.clicked.connect(self.open_mdl_file)
        layout.addWidget(self.open_button)
        
        # Add status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def open_mdl_file(self):
        """Open and process an MDL file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open MDL File", "", "MDL Files (*.mdl);;All Files (*)"
        )
        
        if not file_path:
            return
            
        self.status_bar.showMessage(f"Loading {file_path}...")
        
        try:
            # Create temp directory for extraction
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)
            
            # Use mdl_tool to extract the first LOD
            mdl_tool.parse_mdl_file(
                file_path,
                output_dir=self.temp_dir,
                lod_indices=[0],  # Just extract the first LOD
                skip_binary=True,
                verbose=True
            )
            
            # Find and load the OBJ file
            obj_file = os.path.join(self.temp_dir, "lod_0.obj")
            if os.path.exists(obj_file):
                self.obj_file = obj_file
                if self.gl_widget.load_obj(obj_file):
                    self.status_bar.showMessage(f"Loaded {os.path.basename(file_path)}")
                else:
                    self.status_bar.showMessage("Failed to load the extracted model")
            else:
                self.status_bar.showMessage("Failed to extract OBJ from MDL file")
                
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
            print(f"Error processing MDL: {e}")
    
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