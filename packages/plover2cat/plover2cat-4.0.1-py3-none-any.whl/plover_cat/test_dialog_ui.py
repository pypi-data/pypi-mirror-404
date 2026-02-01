# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'test_dialog.ui'
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
    QDialogButtonBox, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPlainTextEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_testDialog(object):
    def setupUi(self, testDialog):
        if not testDialog.objectName():
            testDialog.setObjectName(u"testDialog")
        testDialog.resize(400, 300)
        self.verticalLayout = QVBoxLayout(testDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label = QLabel(testDialog)
        self.label.setObjectName(u"label")

        self.horizontalLayout_2.addWidget(self.label)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.listSelection = QListWidget(testDialog)
        self.listSelection.setObjectName(u"listSelection")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listSelection.sizePolicy().hasHeightForWidth())
        self.listSelection.setSizePolicy(sizePolicy)
        self.listSelection.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.horizontalLayout.addWidget(self.listSelection)

        self.output = QPlainTextEdit(testDialog)
        self.output.setObjectName(u"output")
        font = QFont()
        font.setFamilies([u"Courier New"])
        font.setPointSize(8)
        self.output.setFont(font)
        self.output.setUndoRedoEnabled(False)
        self.output.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.output.setReadOnly(True)

        self.horizontalLayout.addWidget(self.output)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.runTest = QPushButton(testDialog)
        self.runTest.setObjectName(u"runTest")
        self.runTest.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_3.addWidget(self.runTest)

        self.selectAll = QPushButton(testDialog)
        self.selectAll.setObjectName(u"selectAll")
        self.selectAll.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_3.addWidget(self.selectAll)

        self.unselectAll = QPushButton(testDialog)
        self.unselectAll.setObjectName(u"unselectAll")
        self.unselectAll.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_3.addWidget(self.unselectAll)

        self.buttonBox = QDialogButtonBox(testDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.horizontalLayout_3.addWidget(self.buttonBox)


        self.verticalLayout.addLayout(self.horizontalLayout_3)


        self.retranslateUi(testDialog)
        self.buttonBox.accepted.connect(testDialog.accept)
        self.buttonBox.rejected.connect(testDialog.reject)

        QMetaObject.connectSlotsByName(testDialog)
    # setupUi

    def retranslateUi(self, testDialog):
        testDialog.setWindowTitle(QCoreApplication.translate("testDialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("testDialog", u"Tests:", None))
        self.runTest.setText(QCoreApplication.translate("testDialog", u"Run Selected", None))
        self.selectAll.setText(QCoreApplication.translate("testDialog", u"Select All", None))
        self.unselectAll.setText(QCoreApplication.translate("testDialog", u"Unselect All", None))
    # retranslateUi

