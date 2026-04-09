# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Error_window.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QPushButton,
    QSizePolicy, QSpacerItem, QWidget)
import resources_1_rc

class Ui_error_window_dialog(object):
    def setupUi(self, error_window_dialog):
        if not error_window_dialog.objectName():
            error_window_dialog.setObjectName(u"error_window_dialog")
        error_window_dialog.resize(729, 150)
        error_window_dialog.setMinimumSize(QSize(0, 0))
        error_window_dialog.setMaximumSize(QSize(99999, 99999))
        error_window_dialog.setStyleSheet(u"QDialog{\n"
"	background-color: rgb(64, 64, 64);\n"
"}\n"
"\n"
"QWidget{\n"
"	color: rgb(255, 255, 255);\n"
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
"")
        self.gridLayout = QGridLayout(error_window_dialog)
        self.gridLayout.setObjectName(u"gridLayout")
        self.confirm = QPushButton(error_window_dialog)
        self.confirm.setObjectName(u"confirm")
        self.confirm.setMinimumSize(QSize(0, 0))
        self.confirm.setMaximumSize(QSize(16777215, 99999))

        self.gridLayout.addWidget(self.confirm, 1, 0, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 0, 0, 1, 1)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer_2, 2, 0, 1, 1)


        self.retranslateUi(error_window_dialog)

        QMetaObject.connectSlotsByName(error_window_dialog)
    # setupUi

    def retranslateUi(self, error_window_dialog):
        error_window_dialog.setWindowTitle(QCoreApplication.translate("error_window_dialog", u"ERROR!", None))
        self.confirm.setText(QCoreApplication.translate("error_window_dialog", u"Device, channel, path or data were not choosen properly!", None))
    # retranslateUi

