# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ExternalDepsDialog.ui'
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
    QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)
from usdb_syncer.gui.resources.qt import resources as resources_rc

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        Dialog.resize(784, 573)
        self.verticalLayout_3 = QVBoxLayout(Dialog)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.groupBox_ffmpeg = QGroupBox(Dialog)
        self.groupBox_ffmpeg.setObjectName(u"groupBox_ffmpeg")
        self.verticalLayout = QVBoxLayout(self.groupBox_ffmpeg)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_ffmpeg = QLabel(self.groupBox_ffmpeg)
        self.label_ffmpeg.setObjectName(u"label_ffmpeg")
        self.label_ffmpeg.setTextFormat(Qt.TextFormat.RichText)
        self.label_ffmpeg.setWordWrap(True)
        self.label_ffmpeg.setOpenExternalLinks(True)
        self.label_ffmpeg.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.verticalLayout.addWidget(self.label_ffmpeg)

        self.label_ffmpeg_windows = QLabel(self.groupBox_ffmpeg)
        self.label_ffmpeg_windows.setObjectName(u"label_ffmpeg_windows")
        self.label_ffmpeg_windows.setEnabled(True)
        self.label_ffmpeg_windows.setTextFormat(Qt.TextFormat.RichText)
        self.label_ffmpeg_windows.setWordWrap(True)
        self.label_ffmpeg_windows.setOpenExternalLinks(True)
        self.label_ffmpeg_windows.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.verticalLayout.addWidget(self.label_ffmpeg_windows)

        self.label_ffmpeg_macos = QLabel(self.groupBox_ffmpeg)
        self.label_ffmpeg_macos.setObjectName(u"label_ffmpeg_macos")
        self.label_ffmpeg_macos.setEnabled(True)
        self.label_ffmpeg_macos.setTextFormat(Qt.TextFormat.RichText)
        self.label_ffmpeg_macos.setWordWrap(True)
        self.label_ffmpeg_macos.setOpenExternalLinks(True)
        self.label_ffmpeg_macos.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.verticalLayout.addWidget(self.label_ffmpeg_macos)

        self.label_ffmpeg_linux = QLabel(self.groupBox_ffmpeg)
        self.label_ffmpeg_linux.setObjectName(u"label_ffmpeg_linux")
        self.label_ffmpeg_linux.setEnabled(True)
        self.label_ffmpeg_linux.setTextFormat(Qt.TextFormat.RichText)
        self.label_ffmpeg_linux.setWordWrap(True)

        self.verticalLayout.addWidget(self.label_ffmpeg_linux)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.set_ffmpeg_location = QPushButton(self.groupBox_ffmpeg)
        self.set_ffmpeg_location.setObjectName(u"set_ffmpeg_location")
        icon = QIcon()
        icon.addFile(u":/icons/ffmpeg.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.set_ffmpeg_location.setIcon(icon)

        self.horizontalLayout_2.addWidget(self.set_ffmpeg_location)


        self.verticalLayout.addLayout(self.horizontalLayout_2)


        self.verticalLayout_3.addWidget(self.groupBox_ffmpeg)

        self.groupBox_deno = QGroupBox(Dialog)
        self.groupBox_deno.setObjectName(u"groupBox_deno")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_deno)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_deno = QLabel(self.groupBox_deno)
        self.label_deno.setObjectName(u"label_deno")
        self.label_deno.setTextFormat(Qt.TextFormat.RichText)
        self.label_deno.setWordWrap(True)
        self.label_deno.setOpenExternalLinks(True)
        self.label_deno.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.verticalLayout_2.addWidget(self.label_deno)

        self.label_deno_windows = QLabel(self.groupBox_deno)
        self.label_deno_windows.setObjectName(u"label_deno_windows")
        self.label_deno_windows.setEnabled(True)
        self.label_deno_windows.setTextFormat(Qt.TextFormat.RichText)
        self.label_deno_windows.setWordWrap(True)
        self.label_deno_windows.setOpenExternalLinks(True)
        self.label_deno_windows.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.verticalLayout_2.addWidget(self.label_deno_windows)

        self.label_deno_macos = QLabel(self.groupBox_deno)
        self.label_deno_macos.setObjectName(u"label_deno_macos")
        self.label_deno_macos.setEnabled(True)
        self.label_deno_macos.setTextFormat(Qt.TextFormat.RichText)
        self.label_deno_macos.setWordWrap(True)
        self.label_deno_macos.setOpenExternalLinks(True)
        self.label_deno_macos.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.verticalLayout_2.addWidget(self.label_deno_macos)

        self.label_deno_linux = QLabel(self.groupBox_deno)
        self.label_deno_linux.setObjectName(u"label_deno_linux")
        self.label_deno_linux.setEnabled(True)
        self.label_deno_linux.setTextFormat(Qt.TextFormat.RichText)
        self.label_deno_linux.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.label_deno_linux)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_2)

        self.set_deno_location = QPushButton(self.groupBox_deno)
        self.set_deno_location.setObjectName(u"set_deno_location")
        icon1 = QIcon()
        icon1.addFile(u":/icons/deno.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.set_deno_location.setIcon(icon1)

        self.horizontalLayout_3.addWidget(self.set_deno_location)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)


        self.verticalLayout_3.addWidget(self.groupBox_deno)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.verticalLayout_3.addWidget(self.buttonBox)


        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"External dependencies missing", None))
        self.groupBox_ffmpeg.setTitle(QCoreApplication.translate("Dialog", u"FFmpeg", None))
        self.label_ffmpeg.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-weight:700;\">FFmpeg</span> and FFprobe are required to proceed (see: <a href=\"https://www.ffmpeg.org/\"><span style=\" text-decoration: underline; color:#3586ff;\">https://www.ffmpeg.org/</span></a>).</p></body></html>", None))
        self.label_ffmpeg_windows.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>The recommended way to install FFmpeg is to use a package manager such as <a href=\"https://chocolatey.org/\"><span style=\" text-decoration: underline; color:#3586ff;\">Chocolatey</span></a> (<span style=\" font-family:'Courier New';\">choco install ffmpeg</span>) or <a href=\"https://learn.microsoft.com/en-us/windows/package-manager/winget/\"><span style=\" text-decoration: underline; color:#3586ff;\">winget</span></a> (<span style=\" font-family:'Courier New';\">winget install --id=Gyan.FFmpeg -e</span>).</p><p>Alternatively, download the FFmpeg binaries from <a href=\"https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z\"><span style=\" text-decoration: underline; color:#3586ff;\">Gyan</span></a>, extract the archive and then set the location with the button below. </p></body></html>", None))
        self.label_ffmpeg_macos.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>The recommended way to install FFmpeg is via <a href=\"https://brew.sh/\"><span style=\" text-decoration: underline; color:#3586ff;\">Homebrew</span></a> (<span style=\" font-family:'Courier New';\">brew install ffmpeg</span>).</p></body></html>", None))
        self.label_ffmpeg_linux.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Please install the FFmpeg package through your distribution\u2019s package manager.</p></body></html>", None))
        self.set_ffmpeg_location.setText(QCoreApplication.translate("Dialog", u"Set FFmpeg location...", None))
        self.groupBox_deno.setTitle(QCoreApplication.translate("Dialog", u"Deno JavaScript Runtime", None))
        self.label_deno.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" font-weight:700;\">Deno</span> Javascript Runtime is required to proceed (see <a href=\"https://deno.com/\"><span style=\" text-decoration: underline; color:#3586ff;\">https://deno.com/</span></a>).</p></body></html>", None))
        self.label_deno_windows.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>The recommended way to install Deno is to use a package manager such as <a href=\"https://chocolatey.org/\"><span style=\" text-decoration: underline; color:#3586ff;\">Chocolatey</span></a> (<span style=\" font-family:'Courier New';\">choco install deno</span>) or <a href=\"https://learn.microsoft.com/en-us/windows/package-manager/winget/\"><span style=\" text-decoration: underline; color:#3586ff;\">winget</span></a> (<span style=\" font-family:'Courier New';\">winget install DenoLand.Deno</span>).</p><p>Alternatively, download the Deno binaries from <a href=\"https://github.com/denoland/deno/releases\"><span style=\" text-decoration: underline; color:#3586ff;\">Github</span></a>, extract the archive and then set the location with the button below. </p></body></html>", None))
        self.label_deno_macos.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>The recommended way to install Deno is via <a href=\"https://brew.sh/\"><span style=\" text-decoration: underline; color:#3586ff;\">Homebrew</span></a> (<span style=\" font-family:'Courier New';\">brew install deno</span>).</p></body></html>", None))
        self.label_deno_linux.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>Please install the Deno package through your distribution\u2019s package manager.</p></body></html>", None))
        self.set_deno_location.setText(QCoreApplication.translate("Dialog", u"Set Deno location...", None))
    # retranslateUi

