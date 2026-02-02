# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UsdbUploadDialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
    QSizePolicy, QSpinBox, QSplitter, QTextBrowser,
    QVBoxLayout, QWidget)
from usdb_syncer.gui.resources.qt import resources as resources_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(1129, 955)
        self.verticalLayout = QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.comboBox_songs = QComboBox(Dialog)
        self.comboBox_songs.setObjectName(u"comboBox_songs")

        self.verticalLayout.addWidget(self.comboBox_songs)

        self.splitter = QSplitter(Dialog)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Horizontal)
        self.verticalLayoutWidget = QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayout_remote = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_remote.setObjectName(u"verticalLayout_remote")
        self.verticalLayout_remote.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.verticalLayoutWidget)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_remote.addWidget(self.label)

        self.textBrowser_diff_remote = QTextBrowser(self.verticalLayoutWidget)
        self.textBrowser_diff_remote.setObjectName(u"textBrowser_diff_remote")

        self.verticalLayout_remote.addWidget(self.textBrowser_diff_remote)

        self.splitter.addWidget(self.verticalLayoutWidget)
        self.verticalLayoutWidget_2 = QWidget(self.splitter)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.verticalLayout_local = QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_local.setObjectName(u"verticalLayout_local")
        self.verticalLayout_local.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.verticalLayoutWidget_2)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_local.addWidget(self.label_2)

        self.textBrowser_diff_local = QTextBrowser(self.verticalLayoutWidget_2)
        self.textBrowser_diff_local.setObjectName(u"textBrowser_diff_local")

        self.verticalLayout_local.addWidget(self.textBrowser_diff_local)

        self.splitter.addWidget(self.verticalLayoutWidget_2)

        self.verticalLayout.addWidget(self.splitter)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.checkBox_show_only_changes = QCheckBox(Dialog)
        self.checkBox_show_only_changes.setObjectName(u"checkBox_show_only_changes")

        self.horizontalLayout.addWidget(self.checkBox_show_only_changes)

        self.spinBox_context_lines = QSpinBox(Dialog)
        self.spinBox_context_lines.setObjectName(u"spinBox_context_lines")
        self.spinBox_context_lines.setMaximum(10)
        self.spinBox_context_lines.setValue(3)

        self.horizontalLayout.addWidget(self.spinBox_context_lines)

        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout.addWidget(self.label_3)


        self.horizontalLayout_2.addLayout(self.horizontalLayout)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.horizontalLayout_2.addWidget(self.buttonBox)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Submit changes to USDB", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"Remote (USDB)", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"Local (adapted for upload)", None))
        self.checkBox_show_only_changes.setText(QCoreApplication.translate("Dialog", u"Show only changes with", None))
        self.label_3.setText(QCoreApplication.translate("Dialog", u"context lines", None))
    # retranslateUi

