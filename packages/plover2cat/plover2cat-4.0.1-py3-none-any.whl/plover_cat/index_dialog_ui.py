# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'index_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QCheckBox,
    QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

class Ui_indexDialog(object):
    def setupUi(self, indexDialog):
        if not indexDialog.objectName():
            indexDialog.setObjectName(u"indexDialog")
        indexDialog.resize(448, 305)
        self.horizontalLayout_2 = QHBoxLayout(indexDialog)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(indexDialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.indexChoice = QComboBox(indexDialog)
        self.indexChoice.setObjectName(u"indexChoice")

        self.horizontalLayout_3.addWidget(self.indexChoice)

        self.addNewIndex = QPushButton(indexDialog)
        self.addNewIndex.setObjectName(u"addNewIndex")
        self.addNewIndex.setFocusPolicy(Qt.NoFocus)

        self.horizontalLayout_3.addWidget(self.addNewIndex)


        self.formLayout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_3)

        self.label_2 = QLabel(indexDialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.indexPrefix = QLineEdit(indexDialog)
        self.indexPrefix.setObjectName(u"indexPrefix")

        self.horizontalLayout_4.addWidget(self.indexPrefix)

        self.hideDescript = QCheckBox(indexDialog)
        self.hideDescript.setObjectName(u"hideDescript")
        self.hideDescript.setEnabled(True)
        self.hideDescript.setChecked(True)
        self.hideDescript.setTristate(False)

        self.horizontalLayout_4.addWidget(self.hideDescript)


        self.formLayout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_4)


        self.verticalLayout.addLayout(self.formLayout)

        self.label_3 = QLabel(indexDialog)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout.addWidget(self.label_3)

        self.displayEntries = QTableWidget(indexDialog)
        self.displayEntries.setObjectName(u"displayEntries")
        self.displayEntries.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.displayEntries.setSortingEnabled(True)

        self.verticalLayout.addWidget(self.displayEntries)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label_4 = QLabel(indexDialog)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout.addWidget(self.label_4)

        self.entryText = QLineEdit(indexDialog)
        self.entryText.setObjectName(u"entryText")

        self.horizontalLayout.addWidget(self.entryText)

        self.entryAdd = QPushButton(indexDialog)
        self.entryAdd.setObjectName(u"entryAdd")
        self.entryAdd.setEnabled(False)

        self.horizontalLayout.addWidget(self.entryAdd)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.horizontalLayout_2.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.saveAndInsert = QPushButton(indexDialog)
        self.saveAndInsert.setObjectName(u"saveAndInsert")
        self.saveAndInsert.setEnabled(False)

        self.verticalLayout_2.addWidget(self.saveAndInsert)

        self.saveIndex = QPushButton(indexDialog)
        self.saveIndex.setObjectName(u"saveIndex")

        self.verticalLayout_2.addWidget(self.saveIndex)

        self.buttonBox = QDialogButtonBox(indexDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Vertical)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout_2.addWidget(self.buttonBox)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)


        self.retranslateUi(indexDialog)
        self.buttonBox.rejected.connect(indexDialog.hide)

        QMetaObject.connectSlotsByName(indexDialog)
    # setupUi

    def retranslateUi(self, indexDialog):
        indexDialog.setWindowTitle(QCoreApplication.translate("indexDialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("indexDialog", u"Index:", None))
#if QT_CONFIG(tooltip)
        self.indexChoice.setToolTip(QCoreApplication.translate("indexDialog", u"Indices are numbered starting at 0", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.addNewIndex.setToolTip(QCoreApplication.translate("indexDialog", u"Add another index", None))
#endif // QT_CONFIG(tooltip)
        self.addNewIndex.setText(QCoreApplication.translate("indexDialog", u"Add New Index", None))
        self.label_2.setText(QCoreApplication.translate("indexDialog", u"Prefix:", None))
#if QT_CONFIG(tooltip)
        self.indexPrefix.setToolTip(QCoreApplication.translate("indexDialog", u"Prefix for index entry", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.hideDescript.setToolTip(QCoreApplication.translate("indexDialog", u"Do not show entry description in transcript", None))
#endif // QT_CONFIG(tooltip)
        self.hideDescript.setText(QCoreApplication.translate("indexDialog", u"Hide entry descriptions", None))
        self.label_3.setText(QCoreApplication.translate("indexDialog", u"Entries for index:", None))
#if QT_CONFIG(tooltip)
        self.displayEntries.setToolTip(QCoreApplication.translate("indexDialog", u"Double-click to edit index entry descriptions.", None))
#endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("indexDialog", u"Index entry text:", None))
#if QT_CONFIG(tooltip)
        self.entryText.setToolTip(QCoreApplication.translate("indexDialog", u"Text for the index entry", None))
#endif // QT_CONFIG(tooltip)
        self.entryAdd.setText(QCoreApplication.translate("indexDialog", u"Add new entry", None))
#if QT_CONFIG(tooltip)
        self.saveAndInsert.setToolTip(QCoreApplication.translate("indexDialog", u"Save changes to present index and insert selected entry", None))
#endif // QT_CONFIG(tooltip)
        self.saveAndInsert.setText(QCoreApplication.translate("indexDialog", u"Save && Insert", None))
#if QT_CONFIG(tooltip)
        self.saveIndex.setToolTip(QCoreApplication.translate("indexDialog", u"Save changes to selected index", None))
#endif // QT_CONFIG(tooltip)
        self.saveIndex.setText(QCoreApplication.translate("indexDialog", u"Save", None))
    # retranslateUi

