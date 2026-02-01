# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'shortcut_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QHBoxLayout, QKeySequenceEdit,
    QLabel, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_shortcutDialog(object):
    def setupUi(self, shortcutDialog):
        if not shortcutDialog.objectName():
            shortcutDialog.setObjectName(u"shortcutDialog")
        shortcutDialog.resize(391, 129)
        self.verticalLayout = QVBoxLayout(shortcutDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(shortcutDialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.text_name = QComboBox(shortcutDialog)
        self.text_name.setObjectName(u"text_name")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.text_name)

        self.label_2 = QLabel(shortcutDialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.shortcut = QKeySequenceEdit(shortcutDialog)
        self.shortcut.setObjectName(u"shortcut")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.shortcut)


        self.verticalLayout.addLayout(self.formLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.validate = QPushButton(shortcutDialog)
        self.validate.setObjectName(u"validate")
        self.validate.setContextMenuPolicy(Qt.NoContextMenu)

        self.horizontalLayout.addWidget(self.validate)

        self.buttonBox = QDialogButtonBox(shortcutDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.horizontalLayout.addWidget(self.buttonBox)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(shortcutDialog)
        self.buttonBox.accepted.connect(shortcutDialog.accept)
        self.buttonBox.rejected.connect(shortcutDialog.reject)

        QMetaObject.connectSlotsByName(shortcutDialog)
    # setupUi

    def retranslateUi(self, shortcutDialog):
        shortcutDialog.setWindowTitle(QCoreApplication.translate("shortcutDialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("shortcutDialog", u"Menu Item", None))
#if QT_CONFIG(tooltip)
        self.text_name.setToolTip(QCoreApplication.translate("shortcutDialog", u"Name of menu item", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("shortcutDialog", u"Shortcut", None))
#if QT_CONFIG(tooltip)
        self.shortcut.setToolTip(QCoreApplication.translate("shortcutDialog", u"Click and then press keys for shortcut", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.validate.setToolTip(QCoreApplication.translate("shortcutDialog", u"Check if shortcuts conflict and save", None))
#endif // QT_CONFIG(tooltip)
        self.validate.setText(QCoreApplication.translate("shortcutDialog", u"Validate and save", None))
    # retranslateUi

