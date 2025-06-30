import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton)
from PyQt6.QtGui import QPixmap


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initializeUI()


    def initializeUI(self):
        self.setGeometry(600, 200, 800,600)
        self.setWindowTitle("Progr")
        self.setUpMainWindow()
        self.show()


    def setUpMainWindow(self):
        image_source1 = "/home/ubuntupc/Загрузки/konstr.png"
        image_source2 = "/home/ubuntupc/Загрузки/tabl.png"
        image_source3 = "/home/ubuntupc/Загрузки/downl(1).png"

        with open(image_source1):
            im_konstr = QLabel(self)
            im_konstr.move(200, 200)
            im_konstr1 = QPixmap(image_source1)
            im_konstr.setPixmap(im_konstr1)
        with open(image_source2):
            im_tabl = QLabel(self)
            im_tabl.move(350, 200)
            im_tabl1 = QPixmap(image_source2)
            im_tabl.setPixmap(im_tabl1)
        with open(image_source3):
            im_downl = QLabel(self)
            im_downl.move(490, 180)
            im_downl1 = QPixmap(image_source3)
            im_downl.setPixmap(im_downl1)
            
        but_konstr = QPushButton("Konstructor", self)
        but_konstr.move(210, 310)
        but_tabl = QPushButton("Table", self)
        but_tabl.move(360, 310)
        but_downl = QPushButton("Download", self)
        but_downl.move(525, 310)
        


app = QApplication(sys.argv)
window = MainWindow()
sys.exit(app.exec())
