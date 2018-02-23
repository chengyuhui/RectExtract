import os.path
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cv2
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QPen, QBrush, QPainterPath
from common import cv2pixmap, watershed, imread_u, imwrite_u
import numpy as np

from PyQt5.QtWidgets import *

# Global events
class Communicate(QObject):
    markerUpdated = pyqtSignal(np.ndarray)
    setColor = pyqtSignal(tuple)
    reset = pyqtSignal()
    rectResult = pyqtSignal(tuple)
    save = pyqtSignal()

comm = Communicate()
autoUpdate = False

# Colors BGR
RED = (0, 0, 255)
GREEN = (0, 255, 0)

class DrawScene(QGraphicsScene):
    def __init__(self, img):
        super(DrawScene, self).__init__()

        self.imagePanel = ImageDrawPanel(parent=self, image=img)
        self.addItem(self.imagePanel)
        self.rect = QGraphicsRectItem()
        self.addItem(self.rect)
        self.image = img

        pen = QPen(Qt.DashDotLine)
        pen.setBrush(Qt.red)
        # pen.setWidth(3)
        self.rect.setPen(pen)

        self.setBackgroundBrush(QBrush(Qt.darkGray))

        comm.rectResult.connect(self.drawRect)
        comm.reset.connect(self.resetRect)
        comm.save.connect(self.save)

    def drawRect(self, rect):
        x, y, w, h = rect
        self.rect.setRect(x, y, w, h)

    def resetRect(self):
        self.rect.setRect(0, 0, 0, 0)

    def save(self):
        rect = self.rect.rect()
        x, y, w, h = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())
        if w > 0 and h > 0:
            img = self.image[y:y + h, x:x + w]
            file_name = QFileDialog.getSaveFileName(None, "Save Image", "out", 'PNG Image (*.png)')[0]
            if file_name:
                imwrite_u(file_name, img)

class ImageDrawPanel(QGraphicsPixmapItem):
    def __init__(self, parent=None, image=None):
        super(ImageDrawPanel, self).__init__()

        self.parent = parent
        # Image
        self.image_orig = image
        self.image = image.copy()
        self.setPixmap(cv2pixmap(image))
        # Color
        self.color = RED
        # Points
        self.prev_pt = None
        self.pt = None
        # Marker
        self.markers = np.zeros(image.shape[:2], np.int32)
        # Signal slots
        comm.reset.connect(self.reset)
        comm.setColor.connect(self.setColor)

    def reset(self):
        self.image = self.image_orig.copy()
        self.markers.fill(0)
        self.update()

    def setColor(self, color):
        self.color = color

    def paint(self, painter, option, widget=None):
        painter.drawPixmap(0, 0, cv2pixmap(self.image))

        if self.prev_pt is not None and self.pt[0] >= 0 and self.pt[1] >= 0:
            cv2.line(self.image, self.prev_pt, self.pt, self.color, 5)
            cv2.line(self.markers, self.prev_pt, self.pt, self.get_marker(), 5)
            if autoUpdate:
                comm.markerUpdated.emit(self.markers)
            self.prev_pt = self.pt

    # Handlers
    def mousePressEvent(self, event):
        self.prev_pt = self.get_pt(event)
        self.pt = self.get_pt(event)
        self.update()

    def mouseMoveEvent(self, event):
        self.pt = self.get_pt(event)
        self.update()

    def mouseReleaseEvent(self, event):
        self.prev_pt = None
        comm.markerUpdated.emit(self.markers)
        self.update()

    def get_pt(self, event):
        return int(event.pos().x()), int(event.pos().y())

    def get_marker(self):
        if self.color == RED:
            return 1
        if self.color == GREEN:
            return 2

class CtrlWidget(QWidget):
    def __init__(self):
        super(CtrlWidget, self).__init__()

        self.layout = QVBoxLayout()

        self.addColorBtn('Target Red', RED)
        self.addColorBtn('Exclude Green', GREEN)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(lambda: comm.reset.emit())
        self.layout.addWidget(reset_btn)

        save_btn = QPushButton('Save')
        save_btn.clicked.connect(lambda: comm.save.emit())
        self.layout.addWidget(save_btn)

        check_auto = QCheckBox('Realtime Update')
        # check_auto.setChecked(True)
        check_auto.stateChanged.connect(self.toggleAuto)
        self.layout.addWidget(check_auto)

        self.setLayout(self.layout)

    def addColorBtn(self, label, color):
        button = QPushButton(label)
        button.clicked.connect(lambda: comm.setColor.emit(color))
        self.layout.addWidget(button)

    def toggleAuto(self, state):
        global autoUpdate
        autoUpdate = (state == Qt.Checked)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        image = self.openImage()
        self.draw_scene = DrawScene(image)

        layout = QHBoxLayout()
        layout.addWidget(QGraphicsView(self.draw_scene))
        layout.addWidget(CtrlWidget())

        self.widget = QWidget()
        self.widget.setLayout(layout)

        self.setCentralWidget(self.widget)
        self.setWindowTitle("~~~")

        comm.markerUpdated.connect(lambda marker: comm.rectResult.emit(watershed(image, marker)))

    def openImage(self):
        filename = QFileDialog.getOpenFileName(None, "Open image", ".", "Image Files (*.bmp *.jpg *.png *.tif *.tiff)")[0]
        if filename == '':
            return None
        return imread_u(filename)  # Load as is

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
