import os

import cv2
import os.path
from PyQt4 import QtCore, QtGui
import numpy as np

def cv2pixmap(cvimage):
    height, width, depth = cvimage.shape
    cvimage = cv2.cvtColor(cvimage, cv2.COLOR_BGR2RGB)
    img = QtGui.QImage(cvimage, width, height, depth * width, QtGui.QImage.Format_RGB888)
    return QtGui.QPixmap.fromImage(img)

def watershed(image, marker):
    m = marker.copy()
    cv2.watershed(image, m)
    m[m != 1] = 0
    m *= 255
    points = cv2.findNonZero(m.astype(np.uint8))
    bound_rect = cv2.boundingRect(points)
    # x, y, w, h = bound_rect
    return bound_rect

def read_into_buffer(filename):
    buf = bytearray(os.path.getsize(filename))
    with open(filename, 'rb') as f:
        f.readinto(buf)
    return buf

def imread_u(filename):
    return cv2.imdecode(np.asarray(read_into_buffer(filename)), -1)

def imwrite_u(filename, array):
    retval, buf = cv2.imencode(os.path.splitext(filename)[1], array)
    with open(filename, 'wb') as f:
        f.write(buf)
