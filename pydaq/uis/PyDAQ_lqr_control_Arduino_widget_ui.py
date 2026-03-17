# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'PyDAQ_lqr_control_Arduino_widget.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
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
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QButtonGroup, QComboBox,
    QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton,
    QSizePolicy, QWidget)
import resources_1_rc

class Ui_Arduino_LQR_Control(object):
    def setupUi(self, Arduino_LQR_Control):
        if not Arduino_LQR_Control.objectName():
            Arduino_LQR_Control.setObjectName(u"Arduino_LQR_Control")
        Arduino_LQR_Control.resize(506, 504)
        Arduino_LQR_Control.setStyleSheet(u"QWidget{\n"
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
"    image: url(:/imgs/imgs/drop_up_arrow.png);\n"
"	width: 11px;\n"
"\n"
"	background-color: rgb(0, 79, 0);\n"
"	border-top: 1.5px solid rgb(127, 167, 127);\n"
"	border-left: 1.5px sol"
                        "id rgb(127, 167, 127);\n"
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
"QDoubleSpinBox::down-button:pressed{\n"
"	border: 2px solid rgb(255, 255, 255);\n"
"}\n"
"\n"
"QDoubleSpinBox::down-button:hover{\n"
"	background-color: rgb(0, 50, 0);\n"
"}\n"
"\n"
"QSpinBox{\n"
"	background-color: rgb(77, 77, 77);\n"
"	\n"
"	border-top: 1.5px solid rgb(46, 46, 46);\n"
"	border-left: 1.5px solid rgb(46, 46, 46);\n"
"\n"
"	border-bottom: 1."
                        "5px solid rgb(166, 166, 166);\n"
"	border-right: 1.5px solid rgb(166, 166, 166);\n"
"}\n"
"\n"
"QSpinBox::up-button{\n"
"    image: url(:/imgs/imgs/drop_up_arrow.png);\n"
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
"	border: 2px solid rgb(255, 255, 255)"
                        ";\n"
"}\n"
"\n"
"QSpinBox::down-button:hover{\n"
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
"QPushButto"
                        "n{\n"
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
"	border-right: 1.5px solid rgb(1"
                        "60, 160, 160);\n"
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
"QPushButton#reload_devices{\n"
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
"QPushButton#logo{\n"
"	background-color: rgb(64, 64, 64);\n"
"	border: 0px;\n"
"}\n"
"\n"
"QPushButton#logo:hover{\n"
"	background-color: rgb(166, 166, 166);\n"
""
                        "	border: 1px solid rgb(190, 190, 190) ;\n"
"}\n"
"\n"
"QPushButton#logo:pressed{\n"
"	background-color: rgb(166, 166, 166);\n"
"	border: 1px solid rgb(255, 255, 255) ;\n"
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
"     border: 1px solid rgb(140, 140, 140);\n"
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
"QScrollBar::"
                        "add-line:vertical:pressed {\n"
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
"QScrollBar::handle:vertical:hover {\n"
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
"QTableWidget {\n"
"    background-color: rgb(77, 77, 77);\n"
"    alternate-background-color: rgb(85, 85, 85);\n"
"    gridline-color: rgb(166, 166, 166);\n"
"    color: white;\n"
"    border: 1px solid rgb"
                        "(166, 166, 166);\n"
"    font: 11pt \"Helvetica\";\n"
"}\n"
"\n"
"QTableWidget QLineEdit {\n"
"    background-color: rgb(140, 140, 140);\n"
"    color: black;\n"
"    border: none;\n"
"}\n"
"\n"
"QTableWidget::item:selected {\n"
"    background-color: rgb(0, 79, 0);\n"
"    color: white;\n"
"}\n"
"\n"
"")
        self.gridLayout_3 = QGridLayout(Arduino_LQR_Control)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.widget = QWidget(Arduino_LQR_Control)
        self.widget.setObjectName(u"widget")
        self.gridLayout_2 = QGridLayout(self.widget)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.widget_5 = QWidget(self.widget)
        self.widget_5.setObjectName(u"widget_5")
        self.horizontalLayout_3 = QHBoxLayout(self.widget_5)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.ao_channel_combo = QComboBox(self.widget_5)
        self.ao_channel_combo.setObjectName(u"ao_channel_combo")

        self.horizontalLayout_3.addWidget(self.ao_channel_combo)


        self.gridLayout_2.addWidget(self.widget_5, 2, 2, 1, 1)

        self.widget_10 = QWidget(self.widget)
        self.widget_10.setObjectName(u"widget_10")
        self.gridLayout_8 = QGridLayout(self.widget_10)
        self.gridLayout_8.setObjectName(u"gridLayout_8")
        self.sesh_dur_in = QDoubleSpinBox(self.widget_10)
        self.sesh_dur_in.setObjectName(u"sesh_dur_in")
        self.sesh_dur_in.setMinimumSize(QSize(0, 22))
        self.sesh_dur_in.setMaximumSize(QSize(16777215, 22))
        self.sesh_dur_in.setDecimals(6)
        self.sesh_dur_in.setMaximum(999999999999.000000000000000)
        self.sesh_dur_in.setSingleStep(0.010000000000000)
        self.sesh_dur_in.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        self.sesh_dur_in.setValue(100.000000000000000)

        self.gridLayout_8.addWidget(self.sesh_dur_in, 0, 0, 1, 1)


        self.gridLayout_2.addWidget(self.widget_10, 5, 2, 1, 1)

        self.label_4 = QLabel(self.widget)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_2.addWidget(self.label_4, 2, 0, 1, 1)

        self.label_9 = QLabel(self.widget)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setMinimumSize(QSize(0, 30))
        self.label_9.setMaximumSize(QSize(16777215, 30))

        self.gridLayout_2.addWidget(self.label_9, 6, 0, 1, 1)

        self.widget_2 = QWidget(self.widget)
        self.widget_2.setObjectName(u"widget_2")
        self.gridLayout = QGridLayout(self.widget_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.insert_matrices = QPushButton(self.widget_2)
        self.insert_matrices.setObjectName(u"insert_matrices")
        self.insert_matrices.setMaximumSize(QSize(160, 30))

        self.gridLayout.addWidget(self.insert_matrices, 0, 0, 1, 1)


        self.gridLayout_2.addWidget(self.widget_2, 3, 2, 1, 1)

        self.widget_16 = QWidget(self.widget)
        self.widget_16.setObjectName(u"widget_16")
        self.horizontalLayout_7 = QHBoxLayout(self.widget_16)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.path_line_edit = QLineEdit(self.widget_16)
        self.path_line_edit.setObjectName(u"path_line_edit")
        self.path_line_edit.setMinimumSize(QSize(0, 22))
        self.path_line_edit.setMaximumSize(QSize(16777215, 22))

        self.horizontalLayout_7.addWidget(self.path_line_edit, 0, Qt.AlignmentFlag.AlignVCenter)

        self.path_folder_browse = QPushButton(self.widget_16)
        self.path_folder_browse.setObjectName(u"path_folder_browse")
        self.path_folder_browse.setMinimumSize(QSize(0, 30))
        self.path_folder_browse.setMaximumSize(QSize(16777215, 30))

        self.horizontalLayout_7.addWidget(self.path_folder_browse, 0, Qt.AlignmentFlag.AlignVCenter)


        self.gridLayout_2.addWidget(self.widget_16, 8, 2, 1, 1)

        self.label_14 = QLabel(self.widget)
        self.label_14.setObjectName(u"label_14")

        self.gridLayout_2.addWidget(self.label_14, 3, 0, 1, 1)

        self.label_15 = QLabel(self.widget)
        self.label_15.setObjectName(u"label_15")
        self.label_15.setMinimumSize(QSize(0, 30))
        self.label_15.setMaximumSize(QSize(16777215, 30))

        self.gridLayout_2.addWidget(self.label_15, 4, 0, 1, 1)

        self.widget_4 = QWidget(self.widget)
        self.widget_4.setObjectName(u"widget_4")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.ai_channel_combo = QComboBox(self.widget_4)
        self.ai_channel_combo.setObjectName(u"ai_channel_combo")

        self.horizontalLayout_2.addWidget(self.ai_channel_combo)


        self.gridLayout_2.addWidget(self.widget_4, 1, 2, 1, 1)

        self.label_12 = QLabel(self.widget)
        self.label_12.setObjectName(u"label_12")
        self.label_12.setMinimumSize(QSize(0, 30))
        self.label_12.setMaximumSize(QSize(16777215, 30))

        self.gridLayout_2.addWidget(self.label_12, 8, 0, 1, 1, Qt.AlignmentFlag.AlignVCenter)

        self.label_3 = QLabel(self.widget)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_2.addWidget(self.label_3, 1, 0, 1, 1)

        self.widget_12 = QWidget(self.widget)
        self.widget_12.setObjectName(u"widget_12")
        self.horizontalLayout_5 = QHBoxLayout(self.widget_12)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.yes_save_radio = QRadioButton(self.widget_12)
        self.save_radio_group = QButtonGroup(Arduino_LQR_Control)
        self.save_radio_group.setObjectName(u"save_radio_group")
        self.save_radio_group.addButton(self.yes_save_radio)
        self.yes_save_radio.setObjectName(u"yes_save_radio")
        self.yes_save_radio.setChecked(True)

        self.horizontalLayout_5.addWidget(self.yes_save_radio)

        self.no_save_radio = QRadioButton(self.widget_12)
        self.save_radio_group.addButton(self.no_save_radio)
        self.no_save_radio.setObjectName(u"no_save_radio")

        self.horizontalLayout_5.addWidget(self.no_save_radio)


        self.gridLayout_2.addWidget(self.widget_12, 7, 2, 1, 1, Qt.AlignmentFlag.AlignLeft)

        self.widget_13 = QWidget(self.widget)
        self.widget_13.setObjectName(u"widget_13")
        self.horizontalLayout_6 = QHBoxLayout(self.widget_13)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.yes_rt_plot_radio = QRadioButton(self.widget_13)
        self.plot_radio_group = QButtonGroup(Arduino_LQR_Control)
        self.plot_radio_group.setObjectName(u"plot_radio_group")
        self.plot_radio_group.addButton(self.yes_rt_plot_radio)
        self.yes_rt_plot_radio.setObjectName(u"yes_rt_plot_radio")
        self.yes_rt_plot_radio.setChecked(False)

        self.horizontalLayout_6.addWidget(self.yes_rt_plot_radio)

        self.label_warning = QLabel(self.widget_13)
        self.label_warning.setObjectName(u"label_warning")

        self.horizontalLayout_6.addWidget(self.label_warning)

        self.yes_ate_plot_radio = QRadioButton(self.widget_13)
        self.plot_radio_group.addButton(self.yes_ate_plot_radio)
        self.yes_ate_plot_radio.setObjectName(u"yes_ate_plot_radio")

        self.horizontalLayout_6.addWidget(self.yes_ate_plot_radio)

        self.no_plot_radio = QRadioButton(self.widget_13)
        self.plot_radio_group.addButton(self.no_plot_radio)
        self.no_plot_radio.setObjectName(u"no_plot_radio")
        self.no_plot_radio.setChecked(True)

        self.horizontalLayout_6.addWidget(self.no_plot_radio)


        self.gridLayout_2.addWidget(self.widget_13, 6, 2, 1, 1, Qt.AlignmentFlag.AlignLeft)

        self.widget_3 = QWidget(self.widget)
        self.widget_3.setObjectName(u"widget_3")
        self.horizontalLayout_8 = QHBoxLayout(self.widget_3)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.device_combo = QComboBox(self.widget_3)
        self.device_combo.setObjectName(u"device_combo")
        self.device_combo.setMinimumSize(QSize(0, 22))
        self.device_combo.setMaximumSize(QSize(16777215, 22))

        self.horizontalLayout_8.addWidget(self.device_combo)

        self.reload_devices = QPushButton(self.widget_3)
        self.reload_devices.setObjectName(u"reload_devices")
        self.reload_devices.setMinimumSize(QSize(22, 22))
        self.reload_devices.setMaximumSize(QSize(22, 22))

        self.horizontalLayout_8.addWidget(self.reload_devices)


        self.gridLayout_2.addWidget(self.widget_3, 0, 2, 1, 1)

        self.widget_11 = QWidget(self.widget)
        self.widget_11.setObjectName(u"widget_11")
        self.gridLayout_9 = QGridLayout(self.widget_11)
        self.gridLayout_9.setObjectName(u"gridLayout_9")
        self.Ts_in = QDoubleSpinBox(self.widget_11)
        self.Ts_in.setObjectName(u"Ts_in")
        self.Ts_in.setMinimumSize(QSize(0, 22))
        self.Ts_in.setMaximumSize(QSize(16777215, 22))
        self.Ts_in.setDecimals(6)
        self.Ts_in.setMaximum(999999999999.000000000000000)
        self.Ts_in.setSingleStep(0.010000000000000)
        self.Ts_in.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        self.Ts_in.setValue(1.000000000000000)

        self.gridLayout_9.addWidget(self.Ts_in, 0, 0, 1, 1)


        self.gridLayout_2.addWidget(self.widget_11, 4, 2, 1, 1)

        self.line_2 = QFrame(self.widget)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_2.addWidget(self.line_2, 0, 1, 9, 1)

        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setMinimumSize(QSize(0, 30))
        self.label_2.setMaximumSize(QSize(16777215, 30))

        self.gridLayout_2.addWidget(self.label_2, 0, 0, 1, 1)

        self.label_11 = QLabel(self.widget)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setMinimumSize(QSize(0, 30))
        self.label_11.setMaximumSize(QSize(16777215, 30))

        self.gridLayout_2.addWidget(self.label_11, 7, 0, 1, 1)

        self.label_10 = QLabel(self.widget)
        self.label_10.setObjectName(u"label_10")
        self.label_10.setMinimumSize(QSize(0, 30))
        self.label_10.setMaximumSize(QSize(16777215, 30))

        self.gridLayout_2.addWidget(self.label_10, 5, 0, 1, 1)


        self.gridLayout_3.addWidget(self.widget, 0, 0, 1, 1)

        self.line_3 = QFrame(Arduino_LQR_Control)
        self.line_3.setObjectName(u"line_3")
        self.line_3.setFrameShape(QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QFrame.Shadow.Sunken)

        self.gridLayout_3.addWidget(self.line_3, 1, 0, 1, 1)

        self.start_lqr_control = QPushButton(Arduino_LQR_Control)
        self.start_lqr_control.setObjectName(u"start_lqr_control")
        self.start_lqr_control.setMinimumSize(QSize(130, 30))
        self.start_lqr_control.setMaximumSize(QSize(130, 30))

        self.gridLayout_3.addWidget(self.start_lqr_control, 2, 0, 1, 1, Qt.AlignmentFlag.AlignHCenter)


        self.retranslateUi(Arduino_LQR_Control)

        QMetaObject.connectSlotsByName(Arduino_LQR_Control)
    # setupUi

    def retranslateUi(self, Arduino_LQR_Control):
        Arduino_LQR_Control.setWindowTitle(QCoreApplication.translate("Arduino_LQR_Control", u"Form", None))
        self.label_4.setText(QCoreApplication.translate("Arduino_LQR_Control", u"AO channel (s):", None))
        self.label_9.setText(QCoreApplication.translate("Arduino_LQR_Control", u"Plot data?", None))
        self.insert_matrices.setText(QCoreApplication.translate("Arduino_LQR_Control", u"INSERT MATRICES", None))
        self.path_folder_browse.setText(QCoreApplication.translate("Arduino_LQR_Control", u" BROWSE ", None))
        self.label_14.setText(QCoreApplication.translate("Arduino_LQR_Control", u"A,B and LQR matriz:", None))
        self.label_15.setText(QCoreApplication.translate("Arduino_LQR_Control", u"Sample period (s):", None))
        self.label_12.setText(QCoreApplication.translate("Arduino_LQR_Control", u"Path:", None))
        self.label_3.setText(QCoreApplication.translate("Arduino_LQR_Control", u"AI channel (s):", None))
        self.yes_save_radio.setText(QCoreApplication.translate("Arduino_LQR_Control", u"Yes", None))
        self.no_save_radio.setText(QCoreApplication.translate("Arduino_LQR_Control", u"No", None))
        self.yes_rt_plot_radio.setText(QCoreApplication.translate("Arduino_LQR_Control", u"Real Time", None))
#if QT_CONFIG(tooltip)
        self.label_warning.setToolTip(QCoreApplication.translate("Arduino_LQR_Control", u"<html><head/><body><p><span style=\" font-size:16pt;\">Selecting Real Time may reduce your acquisition performance if you need to collect data at high frequencies ( sample period &lt; 0.05 s ). We suggest plotting at the end of the acquisition if you don't want to be affected.</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.label_warning.setText(QCoreApplication.translate("Arduino_LQR_Control", u"<html><head/><body><p><img src=\":/imgs/imgs/Warning_logo.png\"/></p></body></html>", None))
        self.yes_ate_plot_radio.setText(QCoreApplication.translate("Arduino_LQR_Control", u"At the end", None))
        self.no_plot_radio.setText(QCoreApplication.translate("Arduino_LQR_Control", u"No", None))
#if QT_CONFIG(tooltip)
        self.reload_devices.setToolTip(QCoreApplication.translate("Arduino_LQR_Control", u"<html><head/><body><p>Update COM ports</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.reload_devices.setText("")
        self.label_2.setText(QCoreApplication.translate("Arduino_LQR_Control", u"Device:", None))
        self.label_11.setText(QCoreApplication.translate("Arduino_LQR_Control", u"Save data?", None))
        self.label_10.setText(QCoreApplication.translate("Arduino_LQR_Control", u"Session duration (s):", None))
        self.start_lqr_control.setText(QCoreApplication.translate("Arduino_LQR_Control", u"LQR CONTROL", None))
    # retranslateUi

