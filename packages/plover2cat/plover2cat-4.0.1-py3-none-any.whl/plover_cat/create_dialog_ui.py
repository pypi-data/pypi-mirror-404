# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'create_dialog.ui'
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
    QFormLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_createDialog(object):
    def setupUi(self, createDialog):
        if not createDialog.objectName():
            createDialog.setObjectName(u"createDialog")
        createDialog.resize(407, 153)
        self.verticalLayout_2 = QVBoxLayout(createDialog)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.displayDirectory = QLineEdit(createDialog)
        self.displayDirectory.setObjectName(u"displayDirectory")
        self.displayDirectory.setEnabled(False)
        self.displayDirectory.setReadOnly(True)

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.displayDirectory)

        self.displayName = QLineEdit(createDialog)
        self.displayName.setObjectName(u"displayName")
        self.displayName.setEnabled(False)
        self.displayName.setReadOnly(True)

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.displayName)

        self.getDirectory = QPushButton(createDialog)
        self.getDirectory.setObjectName(u"getDirectory")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.getDirectory.sizePolicy().hasHeightForWidth())
        self.getDirectory.setSizePolicy(sizePolicy)

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.getDirectory)

        self.getName = QPushButton(createDialog)
        self.getName.setObjectName(u"getName")
        sizePolicy.setHeightForWidth(self.getName.sizePolicy().hasHeightForWidth())
        self.getName.setSizePolicy(sizePolicy)

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.FieldRole, self.getName)

        self.label = QLabel(createDialog)
        self.label.setObjectName(u"label")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.label_2 = QLabel(createDialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_2)


        self.verticalLayout_2.addLayout(self.formLayout_2)

        self.buttonBox = QDialogButtonBox(createDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout_2.addWidget(self.buttonBox)


        self.retranslateUi(createDialog)
        self.buttonBox.accepted.connect(createDialog.accept)
        self.buttonBox.rejected.connect(createDialog.reject)

        QMetaObject.connectSlotsByName(createDialog)
    # setupUi

    def retranslateUi(self, createDialog):
        createDialog.setWindowTitle(QCoreApplication.translate("createDialog", u"Dialog", None))
        self.getDirectory.setText(QCoreApplication.translate("createDialog", u"Set transcript directory", None))
        self.getName.setText(QCoreApplication.translate("createDialog", u"Set transcript name", None))
        self.label.setText(QCoreApplication.translate("createDialog", u"Directory:", None))
        self.label_2.setText(QCoreApplication.translate("createDialog", u"Name:", None))
    # retranslateUi

