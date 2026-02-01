# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'tape_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDialog,
    QDialogButtonBox, QHBoxLayout, QListView, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_tapeDialog(object):
    def setupUi(self, tapeDialog):
        if not tapeDialog.objectName():
            tapeDialog.setObjectName(u"tapeDialog")
        tapeDialog.resize(400, 300)
        self.verticalLayout = QVBoxLayout(tapeDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.select_tape = QPushButton(tapeDialog)
        self.select_tape.setObjectName(u"select_tape")

        self.verticalLayout_2.addWidget(self.select_tape)

        self.translate = QPushButton(tapeDialog)
        self.translate.setObjectName(u"translate")

        self.verticalLayout_2.addWidget(self.translate)

        self.translate_ten = QPushButton(tapeDialog)
        self.translate_ten.setObjectName(u"translate_ten")

        self.verticalLayout_2.addWidget(self.translate_ten)

        self.translate_all = QPushButton(tapeDialog)
        self.translate_all.setObjectName(u"translate_all")

        self.verticalLayout_2.addWidget(self.translate_all)

        self.undo_last = QPushButton(tapeDialog)
        self.undo_last.setObjectName(u"undo_last")

        self.verticalLayout_2.addWidget(self.undo_last)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.tape_view = QListView(tapeDialog)
        self.tape_view.setObjectName(u"tape_view")
        self.tape_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tape_view.setProperty(u"showDropIndicator", False)

        self.horizontalLayout.addWidget(self.tape_view)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.buttonBox = QDialogButtonBox(tapeDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(tapeDialog)
        self.buttonBox.accepted.connect(tapeDialog.accept)
        self.buttonBox.rejected.connect(tapeDialog.reject)

        QMetaObject.connectSlotsByName(tapeDialog)
    # setupUi

    def retranslateUi(self, tapeDialog):
        tapeDialog.setWindowTitle(QCoreApplication.translate("tapeDialog", u"Dialog", None))
        self.select_tape.setText(QCoreApplication.translate("tapeDialog", u"Select Tape File", None))
        self.translate.setText(QCoreApplication.translate("tapeDialog", u"Translate 1", None))
        self.translate_ten.setText(QCoreApplication.translate("tapeDialog", u"Translate 10", None))
        self.translate_all.setText(QCoreApplication.translate("tapeDialog", u"Translate All Succeeding", None))
        self.undo_last.setText(QCoreApplication.translate("tapeDialog", u"Undo Last", None))
    # retranslateUi

