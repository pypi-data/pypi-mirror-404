# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'field_dialog.ui'
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
    QDialogButtonBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_fieldDialog(object):
    def setupUi(self, fieldDialog):
        if not fieldDialog.objectName():
            fieldDialog.setObjectName(u"fieldDialog")
        fieldDialog.setWindowModality(Qt.WindowModal)
        fieldDialog.resize(400, 300)
        self.verticalLayout = QVBoxLayout(fieldDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(fieldDialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.fieldName = QLineEdit(fieldDialog)
        self.fieldName.setObjectName(u"fieldName")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.fieldName)

        self.label_2 = QLabel(fieldDialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.fieldValue = QLineEdit(fieldDialog)
        self.fieldValue.setObjectName(u"fieldValue")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.fieldValue)

        self.addNewField = QPushButton(fieldDialog)
        self.addNewField.setObjectName(u"addNewField")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.addNewField)


        self.verticalLayout.addLayout(self.formLayout)

        self.userDictTable = QTableWidget(fieldDialog)
        self.userDictTable.setObjectName(u"userDictTable")
        self.userDictTable.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.userDictTable.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.userDictTable.setTabKeyNavigation(False)
        self.userDictTable.setProperty(u"showDropIndicator", False)
        self.userDictTable.setDragDropOverwriteMode(False)
        self.userDictTable.setAlternatingRowColors(True)
        self.userDictTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.userDictTable.setSortingEnabled(True)

        self.verticalLayout.addWidget(self.userDictTable)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.removeField = QPushButton(fieldDialog)
        self.removeField.setObjectName(u"removeField")
        self.removeField.setAcceptDrops(False)

        self.horizontalLayout.addWidget(self.removeField)

        self.buttonBox = QDialogButtonBox(fieldDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.horizontalLayout.addWidget(self.buttonBox)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(fieldDialog)
        self.buttonBox.accepted.connect(fieldDialog.accept)
        self.buttonBox.rejected.connect(fieldDialog.reject)

        QMetaObject.connectSlotsByName(fieldDialog)
    # setupUi

    def retranslateUi(self, fieldDialog):
        fieldDialog.setWindowTitle(QCoreApplication.translate("fieldDialog", u"Field Editor", None))
        self.label.setText(QCoreApplication.translate("fieldDialog", u"Field name:", None))
#if QT_CONFIG(tooltip)
        self.fieldName.setToolTip(QCoreApplication.translate("fieldDialog", u"Identifier for field, best be ASCII characters", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("fieldDialog", u"Field value:", None))
#if QT_CONFIG(tooltip)
        self.fieldValue.setToolTip(QCoreApplication.translate("fieldDialog", u"Text value for field, appears in transcript. If left blank, field name appears in text.", None))
#endif // QT_CONFIG(tooltip)
        self.addNewField.setText(QCoreApplication.translate("fieldDialog", u"Add new field", None))
#if QT_CONFIG(tooltip)
        self.userDictTable.setToolTip(QCoreApplication.translate("fieldDialog", u"Double-click cells to edit field values.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.removeField.setToolTip(QCoreApplication.translate("fieldDialog", u"Removes selected field from table", None))
#endif // QT_CONFIG(tooltip)
        self.removeField.setText(QCoreApplication.translate("fieldDialog", u"Remove field", None))
#if QT_CONFIG(tooltip)
        self.buttonBox.setToolTip("")
#endif // QT_CONFIG(tooltip)
    # retranslateUi

