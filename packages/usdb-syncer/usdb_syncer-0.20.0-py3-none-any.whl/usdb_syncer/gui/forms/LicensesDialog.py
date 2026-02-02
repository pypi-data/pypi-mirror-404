# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'LicensesDialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QSizePolicy, QTextBrowser, QVBoxLayout, QWidget)

class Ui_licenses(object):
    def setupUi(self, licenses):
        if not licenses.objectName():
            licenses.setObjectName(u"licenses")
        licenses.resize(750, 380)
        self.verticalLayout = QVBoxLayout(licenses)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.license_textBrowser = QTextBrowser(licenses)
        self.license_textBrowser.setObjectName(u"license_textBrowser")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.license_textBrowser.sizePolicy().hasHeightForWidth())
        self.license_textBrowser.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.license_textBrowser)

        self.close_buttonBox = QDialogButtonBox(licenses)
        self.close_buttonBox.setObjectName(u"close_buttonBox")
        self.close_buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.close_buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.verticalLayout.addWidget(self.close_buttonBox)


        self.retranslateUi(licenses)
        self.close_buttonBox.accepted.connect(licenses.accept)
        self.close_buttonBox.rejected.connect(licenses.reject)

        QMetaObject.connectSlotsByName(licenses)
    # setupUi

    def retranslateUi(self, licenses):
        licenses.setWindowTitle(QCoreApplication.translate("licenses", u"Third-Party-License Information", None))
    # retranslateUi

