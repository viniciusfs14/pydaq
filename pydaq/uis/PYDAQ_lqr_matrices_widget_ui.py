# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PYDAQ_lqr_matrices_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHeaderView,
    QLabel, QPushButton, QScrollArea, QSizePolicy,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)
import resources_1_rc

class Ui_Select_LQR_Matrices_Widget(object):
    def setupUi(self, Select_LQR_Matrices_Widget):
        if not Select_LQR_Matrices_Widget.objectName():
            Select_LQR_Matrices_Widget.setObjectName(u"Select_LQR_Matrices_Widget")
        Select_LQR_Matrices_Widget.resize(805, 585)
        Select_LQR_Matrices_Widget.setStyleSheet(u"QWidget{\n"
"	background-color: rgb(64, 64, 64);\n"
"}\n"
"\n"
"QTabWidget::pane { \n"
"   border: 1px solid rgb(166, 166, 166);\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"  	background-color: rgb(77, 77, 77);\n"
" }\n"
"\n"
" QTabBar::tab:selected {\n"
"  	background-color: rgb(140, 140, 140);\n"
"	padding-top: 2px;\n"
"	padding-bottom: 2px;\n"
"	padding-left: 12px;\n"
"	padding-right: 12px;\n"
" }\n"
"\n"
" QTabBar::tab:selected:hover {\n"
"  	background-color: rgb(140, 140, 140);\n"
"	padding-top: 2px;\n"
"	padding-bottom: 2px;\n"
"	padding-left: 12px;\n"
"	padding-right: 12px;\n"
" }\n"
"\n"
" QTabBar::tab:hover {\n"
"  	background-color: rgb(109, 109, 109);\n"
"	padding-top: 2px;\n"
"	padding-bottom: 2px;\n"
"	padding-left: 12px;\n"
"	padding-right: 12px;\n"
" }\n"
"\n"
" QTabBar::tab:middle {\n"
"	border-right: 1px dashed rgb(166, 166, 166);\n"
"	border-left: 1px dashed rgb(166, 166, 166);\n"
"	padding-top: 2px;\n"
"	padding-bottom: 2px;\n"
"	padding-left: 12px;\n"
"	padding-right: 12px;\n"
" }\n"
"\n"
" QTabBar:"
                        ":tab:last {\n"
"	border-top-right-radius: 10px;\n"
"	padding-top: 2px;\n"
"	padding-bottom: 2px;\n"
"	padding-left: 12px;\n"
"	padding-right: 12px;\n"
" }\n"
"\n"
" QTabBar::tab:first {\n"
"	border-top-left-radius: 10px;\n"
"	padding-top: 2px;\n"
"	padding-bottom: 2px;\n"
"	padding-left: 12px;\n"
"	padding-right: 12px;\n"
" }\n"
"\n"
"\n"
"QComboBox QAbstractItemView {\n"
"    background-color: rgb(77, 77, 77);\n"
"}\n"
"\n"
"QComboBox QAbstractItemView::item:focus{\n"
"    background-color: rgb(140, 140, 140);\n"
"}\n"
"\n"
"QDoubleSpinBox{\n"
"	background-color: rgb(77, 77, 77);\n"
"	\n"
"	border-top: 1.5px solid rgb(46, 46, 46);\n"
"	border-left: 1.5px solid rgb(46, 46, 46);\n"
"\n"
"	border-bottom: 1.5px solid rgb(166, 166, 166);\n"
"	border-right: 1.5px solid rgb(166, 166, 166);\n"
"}\n"
"\n"
"QDoubleSpinBox::up-button{\n"
"    image: url(:/imgs/drop_up_arrow.png);\n"
"	width: 11px;\n"
"\n"
"	background-color: rgb(0, 79, 0);\n"
"	border-top: 1.5px solid rgb(127, 167, 127);\n"
"	border-left: 1.5px solid rg"
                        "b(127, 167, 127);\n"
"\n"
"	border-bottom: 1.5px solid rgb(0, 0, 0);\n"
"	border-right: 1.5px solid rgb(0, 0, 0);\n"
"}\n"
"\n"
"QDoubleSpinBox::up-button:pressed{\n"
"	border: 2px solid rgb(255, 255, 255);\n"
"}\n"
"\n"
"QDoubleSpinBox::up-button:hover{\n"
"	background-color: rgb(0, 50, 0);\n"
"}\n"
"\n"
"QDoubleSpinBox::down-button{\n"
"    image: url(:/imgs/drop_down_arrow.png);\n"
"	width: 11px;\n"
"\n"
"	background-color: rgb(0, 79, 0);\n"
"	border-top: 1.5px solid rgb(127, 167, 127);\n"
"	border-left: 1.5px solid rgb(127, 167, 127);\n"
"\n"
"	border-bottom: 1.5px solid rgb(0, 0, 0);\n"
"	border-right: 1.5px solid rgb(0, 0, 0);\n"
"}\n"
"\n"
"QDoubleSpinBox::down-button:pressed{\n"
"	border: 2px solid rgb(255, 255, 255);\n"
"}\n"
"\n"
"QDoubleSpinBox::down-button:hover{\n"
"	background-color: rgb(0, 50, 0);\n"
"}\n"
"\n"
"QWidget#centralwidget{\n"
"	background-color: rgb(64, 64, 64);\n"
"}\n"
"\n"
"QWidget{\n"
"	color: rgb(255, 255, 255);\n"
"}\n"
"\n"
"QComboBox{\n"
"	background-color: rgb(77, 77, 77);\n"
""
                        "	\n"
"	border-top: 1.5px solid rgb(46, 46, 46);\n"
"	border-left: 1.5px solid rgb(46, 46, 46);\n"
"\n"
"	border-bottom: 1.5px solid rgb(166, 166, 166);\n"
"	border-right: 1.5px solid rgb(166, 166, 166);\n"
"}\n"
"\n"
"\n"
"QComboBox::drop-down{\n"
"	image: url(:/imgs/imgs/drop_down_arrow.png);\n"
"	width: 11px;\n"
"\n"
"	background-color: rgb(0, 79, 0);\n"
"	border-top: 2px solid rgb(127, 167, 127);\n"
"	border-left: 2px solid rgb(127, 167, 127);\n"
"\n"
"	border-bottom: 2px solid rgb(0, 0, 0);\n"
"	border-right: 2px solid rgb(0, 0, 0);\n"
"}\n"
"\n"
"QComboBox::drop-down:hover{\n"
"	background-color: rgb(0, 50, 0);\n"
"}\n"
"\n"
"QComboBox::drop-down:pressed{\n"
"	border: 2px solid rgb(255, 255, 255);\n"
"}\n"
"\n"
"QPushButton{\n"
"	background-color: rgb(0, 79, 0);\n"
"\n"
"	border-top: 1.5px solid rgb(127, 167, 127);\n"
"	border-left: 1.5px solid rgb(127, 167, 127);\n"
"\n"
"	border-bottom: 1.5px solid rgb(0, 0, 0);\n"
"	border-right: 1.5px solid rgb(0, 0, 0);\n"
"\n"
"	\n"
"	font: 12pt \"Helvetica\";\n"
"	"
                        "text-align:center;\n"
"}\n"
"\n"
"QWidget{\n"
"	font: 12pt \"Helvetica\";\n"
"}\n"
"\n"
"QPushButton:hover{\n"
"	background-color: rgb(0, 50, 0);\n"
"}\n"
"\n"
"QPushButton:pressed{\n"
"	border: 2px solid rgb(255, 255, 255);\n"
"}\n"
"\n"
"QLineEdit{\n"
"	background-color: rgb(77, 77, 77);\n"
"	border-top: 1.5px solid rgb(46, 46, 46);\n"
"	border-left: 1.5px solid rgb(46, 46, 46);\n"
"\n"
"	border-bottom: 1.5px solid rgb(166, 166, 166);\n"
"	border-right: 1.5px solid rgb(166, 166, 166);\n"
"}\n"
"\n"
"QRadioButton::indicator{\n"
"	border-radius: 6px;\n"
"	border-top: 1.5px solid rgb(0, 0, 0);\n"
"	border-left: 1.5px solid rgb(0, 0, 0);\n"
"\n"
"	border-bottom: 1.5px solid rgb(160, 160, 160);\n"
"	border-right: 1.5px solid rgb(160, 160, 160);\n"
"}\n"
"\n"
"QRadioButton::indicator::checked{\n"
"	background-color: white;\n"
"}\n"
"\n"
"QRadioButton::indicator::unchecked:hover{\n"
"	background-color: #9F9F9F;\n"
"}\n"
"\n"
"QRadioButton::indicator::pressed{\n"
"	border: 1.5px solid #505050\n"
"}\n"
"\n"
"QPushBut"
                        "ton#reload_devices{\n"
"	image: url(:/imgs/imgs/reload.png);\n"
"	width: 11px;\n"
"	background-color: rgb(0, 79, 0);\n"
"\n"
"	border-top: 1.5px solid rgb(127, 167, 127);\n"
"	border-left: 1.5px solid rgb(127, 167, 127);\n"
"\n"
"	border-bottom: 1.5px solid rgb(0, 0, 0);\n"
"	border-right: 1.5px solid rgb(0, 0, 0);\n"
"\n"
"	\n"
"	font: 12pt \"Helvetica\";\n"
"	text-align:center;\n"
"}\n"
"\n"
"QPushButton#reload_devices:hover{\n"
"	background-color: rgb(0, 50, 0);\n"
"}\n"
"\n"
"QPushButton#reload_devices:pressed{\n"
"	border: 2px solid rgb(255, 255, 255);\n"
"}\n"
"\n"
"QSpinBox{\n"
"	background-color: rgb(77, 77, 77);\n"
"	\n"
"	border-top: 1.5px solid rgb(46, 46, 46);\n"
"	border-left: 1.5px solid rgb(46, 46, 46);\n"
"\n"
"	border-bottom: 1.5px solid rgb(166, 166, 166);\n"
"	border-right: 1.5px solid rgb(166, 166, 166);\n"
"}\n"
"\n"
"QSpinBox::up-button{\n"
"    image: url(:/imgs/imgs/drop_up_arrow.png);\n"
"	width: 11px;\n"
"\n"
"	background-color: rgb(0, 79, 0);\n"
"	border-top: 1.5px solid rgb(127, 167"
                        ", 127);\n"
"	border-left: 1.5px solid rgb(127, 167, 127);\n"
"\n"
"	border-bottom: 1.5px solid rgb(0, 0, 0);\n"
"	border-right: 1.5px solid rgb(0, 0, 0);\n"
"}\n"
"\n"
"QSpinBox::up-button:pressed{\n"
"	border: 2px solid rgb(255, 255, 255);\n"
"}\n"
"\n"
"QSpinBox::up-button:hover{\n"
"	background-color: rgb(0, 50, 0);\n"
"}\n"
"\n"
"QSpinBox::down-button{\n"
"    image: url(:/imgs/imgs/drop_down_arrow.png);\n"
"	width: 11px;\n"
"\n"
"	background-color: rgb(0, 79, 0);\n"
"	border-top: 1.5px solid rgb(127, 167, 127);\n"
"	border-left: 1.5px solid rgb(127, 167, 127);\n"
"\n"
"	border-bottom: 1.5px solid rgb(0, 0, 0);\n"
"	border-right: 1.5px solid rgb(0, 0, 0);\n"
"}\n"
"\n"
"QSpinBox::down-button:pressed{\n"
"	border: 2px solid rgb(255, 255, 255);\n"
"}\n"
"\n"
"QSpinBox::down-button:hover{\n"
"	background-color: rgb(0, 50, 0);\n"
"}\n"
"\n"
"QTableWidget {\n"
"    background-color: rgb(77, 77, 77);\n"
"    gridline-color: rgb(166, 166, 166);\n"
"    color: white; /* All text white */\n"
"    border: 1px solid "
                        "rgb(166, 166, 166);\n"
"    font: 11pt \"Helvetica\";\n"
"    selection-background-color: rgb(110, 110, 110); \n"
"    selection-color: white;\n"
"}\n"
"\n"
"QHeaderView::section {\n"
"    background-color: rgb(77, 77, 77);\n"
"    color: white;\n"
"    border: 1px solid rgb(166, 166, 166);\n"
"}\n"
"\n"
"QTableWidget QLineEdit {\n"
"    background-color: rgb(90, 90, 90); \n"
"    color: white;\n"
"    border: 1px solid rgb(166, 166, 166);\n"
"}\n"
"\n"
"QTableWidget::item {\n"
"    color: white;\n"
"}\n"
"\n"
"QTableWidget::item:selected {\n"
"    background-color: rgb(110, 110, 110);\n"
"    color: white;\n"
"}\n"
"\n"
"QScrollBar:vertical {\n"
"     border: 1px solid rgb(140, 140, 140);\n"
"     background: rgb(140, 140, 140);\n"
"     width: 17px;\n"
"     margin: 17px 0 17px 0;\n"
" }\n"
"QScrollBar::handle:vertical {\n"
"     background: rgb(0, 79, 0);\n"
"     min-height: 20px;\n"
" }\n"
"QScrollBar::add-line:vertical {\n"
"	image: url(:/imgs/imgs/drop_down_arrow.png);\n"
"     border: 1px solid rgb(140"
                        ", 140, 140);\n"
"     background: rgb(0, 79, 0);\n"
"     height: 15px;\n"
"     subcontrol-position: bottom;\n"
"     subcontrol-origin: margin;\n"
" }\n"
"\n"
"QScrollBar::sub-line:vertical {\n"
"	image: url(:/imgs/imgs/drop_up_arrow.png);\n"
"     border: 1px solid rgb(140, 140, 140);\n"
"     background: rgb(0, 79, 0);\n"
"     height: 15px;\n"
"     subcontrol-position: top;\n"
"     subcontrol-origin: margin;\n"
" }\n"
"\n"
"QScrollBar::add-line:vertical:pressed {\n"
"    border: 1px solid rgb(255, 255, 255);\n"
"	background: rgb(0, 79, 0)\n"
" }\n"
"\n"
"QScrollBar::sub-line:vertical:pressed {\n"
"	border: 1px solid rgb(255, 255, 255);\n"
"	background: rgb(0, 79, 0)\n"
" }\n"
"\n"
"QScrollBar::add-line:vertical:hover {\n"
"     background-color: rgb(0, 50, 0);\n"
" }\n"
"\n"
"QScrollBar::sub-line:vertical:hover {\n"
"    background-color: rgb(0, 50, 0);\n"
" }\n"
"\n"
"QScrollBar::handle:vertical:pressed {\n"
"    border: 1px solid rgb(255, 255, 255);\n"
"	background: rgb(0, 79, 0)\n"
" }\n"
"\n"
"QScro"
                        "llBar::handle:vertical:hover {\n"
"    background-color: rgb(0, 50, 0);\n"
" }\n"
"\n"
"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {\n"
"     background: none;\n"
" }\n"
"\n"
"QScrollArea{\n"
"	border: none;\n"
"}\n"
"\n"
"QScrollBar:horizontal {\n"
"    border: 1px solid rgb(140, 140, 140);\n"
"    background: rgb(140, 140, 140);\n"
"    height: 17px;\n"
"    margin: 0 17px 0 17px; \n"
"}\n"
"\n"
"QScrollBar::handle:horizontal {\n"
"    background: rgb(0, 79, 0);\n"
"    min-width: 20px;\n"
"}\n"
"\n"
"QScrollBar::add-line:horizontal {\n"
"    image: url(:/imgs/imgs/drop_right_arrow.png); \n"
"    border: 1px solid rgb(140, 140, 140);\n"
"    background: rgb(0, 79, 0);\n"
"    width: 15px;\n"
"    subcontrol-position: right;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"\n"
"QScrollBar::sub-line:horizontal {\n"
"    image: url(:/imgs/imgs/drop_left_arrow.png);\n"
"    border: 1px solid rgb(140, 140, 140);\n"
"    background: rgb(0, 79, 0);\n"
"    width: 15px;\n"
"    subcontrol-position: lef"
                        "t;\n"
"    subcontrol-origin: margin;\n"
"}\n"
"\n"
"QScrollBar::add-line:horizontal:pressed, QScrollBar::sub-line:horizontal:pressed, QScrollBar::handle:horizontal:pressed {\n"
"    border: 1px solid rgb(255, 255, 255);\n"
"    background: rgb(0, 79, 0);\n"
"}\n"
"\n"
"QScrollBar::add-line:horizontal:hover, QScrollBar::sub-line:horizontal:hover, QScrollBar::handle:horizontal:hover {\n"
"    background-color: rgb(0, 50, 0);\n"
"}\n"
"\n"
"QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {\n"
"    background: none;\n"
"}\n"
"")
        Select_LQR_Matrices_Widget.setLocale(QLocale(QLocale.English, QLocale.World))
        self.gridLayout = QGridLayout(Select_LQR_Matrices_Widget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.scrollArea = QScrollArea(Select_LQR_Matrices_Widget)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setLocale(QLocale(QLocale.English, QLocale.World))
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 770, 919))
        self.gridLayout_2 = QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.Matrix_Q = QWidget(self.scrollAreaWidgetContents)
        self.Matrix_Q.setObjectName(u"Matrix_Q")
        self.verticalLayout_3 = QVBoxLayout(self.Matrix_Q)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.labelQ = QLabel(self.Matrix_Q)
        self.labelQ.setObjectName(u"labelQ")

        self.verticalLayout_3.addWidget(self.labelQ)

        self.tableQ = QTableWidget(self.Matrix_Q)
        self.tableQ.setObjectName(u"tableQ")

        self.verticalLayout_3.addWidget(self.tableQ)


        self.gridLayout_2.addWidget(self.Matrix_Q, 6, 0, 1, 1)

        self.Matrix_B = QWidget(self.scrollAreaWidgetContents)
        self.Matrix_B.setObjectName(u"Matrix_B")
        self.verticalLayout_2 = QVBoxLayout(self.Matrix_B)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.labelB = QLabel(self.Matrix_B)
        self.labelB.setObjectName(u"labelB")

        self.verticalLayout_2.addWidget(self.labelB)

        self.tableB = QTableWidget(self.Matrix_B)
        self.tableB.setObjectName(u"tableB")

        self.verticalLayout_2.addWidget(self.tableB)


        self.gridLayout_2.addWidget(self.Matrix_B, 5, 0, 1, 1)

        self.line_header = QFrame(self.scrollAreaWidgetContents)
        self.line_header.setObjectName(u"line_header")
        self.line_header.setFrameShape(QFrame.Shape.HLine)
        self.line_header.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_2.addWidget(self.line_header, 2, 0, 1, 1)

        self.Matrix_A = QWidget(self.scrollAreaWidgetContents)
        self.Matrix_A.setObjectName(u"Matrix_A")
        self.verticalLayout = QVBoxLayout(self.Matrix_A)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.labelA = QLabel(self.Matrix_A)
        self.labelA.setObjectName(u"labelA")

        self.verticalLayout.addWidget(self.labelA)

        self.tableA = QTableWidget(self.Matrix_A)
        self.tableA.setObjectName(u"tableA")

        self.verticalLayout.addWidget(self.tableA)


        self.gridLayout_2.addWidget(self.Matrix_A, 4, 0, 1, 1)

        self.label_3 = QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_2.addWidget(self.label_3, 9, 0, 1, 1)

        self.Matrix_R = QWidget(self.scrollAreaWidgetContents)
        self.Matrix_R.setObjectName(u"Matrix_R")
        self.verticalLayout_4 = QVBoxLayout(self.Matrix_R)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.labelR = QLabel(self.Matrix_R)
        self.labelR.setObjectName(u"labelR")

        self.verticalLayout_4.addWidget(self.labelR)

        self.tableR = QTableWidget(self.Matrix_R)
        self.tableR.setObjectName(u"tableR")

        self.verticalLayout_4.addWidget(self.tableR)


        self.gridLayout_2.addWidget(self.Matrix_R, 7, 0, 1, 1)

        self.label_2 = QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 3, 0, 1, 1)

        self.header = QWidget(self.scrollAreaWidgetContents)
        self.header.setObjectName(u"header")
        self.gridLayout_3 = QGridLayout(self.header)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.label_states = QLabel(self.header)
        self.label_states.setObjectName(u"label_states")

        self.gridLayout_3.addWidget(self.label_states, 1, 0, 1, 1)

        self.spin_states = QSpinBox(self.header)
        self.spin_states.setObjectName(u"spin_states")
        self.spin_states.setMinimum(1)

        self.gridLayout_3.addWidget(self.spin_states, 1, 1, 1, 1)

        self.spin_inputs = QSpinBox(self.header)
        self.spin_inputs.setObjectName(u"spin_inputs")
        self.spin_inputs.setMinimum(1)

        self.gridLayout_3.addWidget(self.spin_inputs, 1, 3, 1, 1)

        self.label_input = QLabel(self.header)
        self.label_input.setObjectName(u"label_input")

        self.gridLayout_3.addWidget(self.label_input, 1, 2, 1, 1)


        self.gridLayout_2.addWidget(self.header, 1, 0, 1, 1)

        self.line_bottom = QFrame(self.scrollAreaWidgetContents)
        self.line_bottom.setObjectName(u"line_bottom")
        self.line_bottom.setFrameShape(QFrame.Shape.HLine)
        self.line_bottom.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_2.addWidget(self.line_bottom, 14, 0, 1, 1)

        self.Matrix_D = QWidget(self.scrollAreaWidgetContents)
        self.Matrix_D.setObjectName(u"Matrix_D")
        self.verticalLayout_6 = QVBoxLayout(self.Matrix_D)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.labelD = QLabel(self.Matrix_D)
        self.labelD.setObjectName(u"labelD")

        self.verticalLayout_6.addWidget(self.labelD)

        self.tableD = QTableWidget(self.Matrix_D)
        self.tableD.setObjectName(u"tableD")

        self.verticalLayout_6.addWidget(self.tableD)


        self.gridLayout_2.addWidget(self.Matrix_D, 11, 0, 1, 1)

        self.label = QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName(u"label")

        self.gridLayout_2.addWidget(self.label, 0, 0, 1, 1)

        self.Matrix_C = QWidget(self.scrollAreaWidgetContents)
        self.Matrix_C.setObjectName(u"Matrix_C")
        self.verticalLayout_5 = QVBoxLayout(self.Matrix_C)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.labelC = QLabel(self.Matrix_C)
        self.labelC.setObjectName(u"labelC")

        self.verticalLayout_5.addWidget(self.labelC)

        self.tableC = QTableWidget(self.Matrix_C)
        self.tableC.setObjectName(u"tableC")

        self.verticalLayout_5.addWidget(self.tableC)


        self.gridLayout_2.addWidget(self.Matrix_C, 10, 0, 1, 1)

        self.line = QFrame(self.scrollAreaWidgetContents)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_2.addWidget(self.line, 8, 0, 1, 1)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.gridLayout.addWidget(self.scrollArea, 1, 0, 1, 1)

        self.bottom = QWidget(Select_LQR_Matrices_Widget)
        self.bottom.setObjectName(u"bottom")
        self.gridLayout_6 = QGridLayout(self.bottom)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.select_button = QPushButton(self.bottom)
        self.select_button.setObjectName(u"select_button")
        self.select_button.setMinimumSize(QSize(200, 0))
        self.select_button.setMaximumSize(QSize(200, 16777215))

        self.gridLayout_6.addWidget(self.select_button, 1, 0, 1, 1)


        self.gridLayout.addWidget(self.bottom, 2, 0, 1, 1)


        self.retranslateUi(Select_LQR_Matrices_Widget)

        QMetaObject.connectSlotsByName(Select_LQR_Matrices_Widget)
    # setupUi

    def retranslateUi(self, Select_LQR_Matrices_Widget):
        Select_LQR_Matrices_Widget.setWindowTitle(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"Discrete LQR Matrices", None))
        self.labelQ.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"Matrix Q (State Cost)", None))
        self.labelB.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"Matrix B_d (Input Matrix)", None))
        self.labelA.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"Matrix A_d (State Matrix)", None))
#if QT_CONFIG(tooltip)
        self.label_3.setToolTip(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"<html><head/><body><p>Used only to compute output: y[k] = C_d x[k] + D_d u[k]</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"Output Model (for visualization only)", None))
        self.labelR.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"Matrix R (Input Cost)", None))
        self.label_2.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"LQR Design (Discrete)", None))
        self.label_states.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"States (n):", None))
        self.label_input.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"Inputs (m):", None))
        self.labelD.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"Matrix D_d (Feedthrough Matrix)", None))
        self.label.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"All matrices must be in discrete-time form: x[k+1] = A_d x[k] + B_d u[k]", None))
        self.labelC.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"Matrix C_d (Output Matrix)", None))
        self.select_button.setText(QCoreApplication.translate("Select_LQR_Matrices_Widget", u"SELECT LQR MATRICES", None))
    # retranslateUi

