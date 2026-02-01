# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'suggest_dialog.ui'
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
    QDialogButtonBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSpinBox,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

class Ui_suggestDialog(object):
    def setupUi(self, suggestDialog):
        if not suggestDialog.objectName():
            suggestDialog.setObjectName(u"suggestDialog")
        suggestDialog.resize(814, 217)
        self.horizontalLayout = QHBoxLayout(suggestDialog)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label_6 = QLabel(suggestDialog)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.searchType = QComboBox(suggestDialog)
        self.searchType.addItem("")
        self.searchType.addItem("")
        self.searchType.addItem("")
        self.searchType.setObjectName(u"searchType")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.searchType)

        self.scowlSize = QComboBox(suggestDialog)
        self.scowlSize.addItem("")
        self.scowlSize.addItem("")
        self.scowlSize.addItem("")
        self.scowlSize.addItem("")
        self.scowlSize.addItem("")
        self.scowlSize.addItem("")
        self.scowlSize.addItem("")
        self.scowlSize.addItem("")
        self.scowlSize.addItem("")
        self.scowlSize.addItem("")
        self.scowlSize.setObjectName(u"scowlSize")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.scowlSize)

        self.label = QLabel(suggestDialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label)

        self.minOccur = QSpinBox(suggestDialog)
        self.minOccur.setObjectName(u"minOccur")
        self.minOccur.setMinimum(1)
        self.minOccur.setValue(3)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.minOccur)

        self.label_2 = QLabel(suggestDialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.minNgram = QSpinBox(suggestDialog)
        self.minNgram.setObjectName(u"minNgram")
        self.minNgram.setMinimum(2)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.minNgram)

        self.label_3 = QLabel(suggestDialog)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.maxNgram = QSpinBox(suggestDialog)
        self.maxNgram.setObjectName(u"maxNgram")
        self.maxNgram.setMinimum(2)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.maxNgram)

        self.label_7 = QLabel(suggestDialog)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_7)

        self.detect = QPushButton(suggestDialog)
        self.detect.setObjectName(u"detect")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.detect)


        self.horizontalLayout_2.addLayout(self.formLayout)

        self.displaySuggest = QTableWidget(suggestDialog)
        self.displaySuggest.setObjectName(u"displaySuggest")

        self.horizontalLayout_2.addWidget(self.displaySuggest)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.toDictionary = QPushButton(suggestDialog)
        self.toDictionary.setObjectName(u"toDictionary")

        self.verticalLayout_2.addWidget(self.toDictionary)

        self.buttonBox = QDialogButtonBox(suggestDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Vertical)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)

        self.verticalLayout_2.addWidget(self.buttonBox)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)


        self.horizontalLayout.addLayout(self.horizontalLayout_2)


        self.retranslateUi(suggestDialog)
        self.buttonBox.accepted.connect(suggestDialog.accept)
        self.buttonBox.rejected.connect(suggestDialog.reject)

        self.scowlSize.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(suggestDialog)
    # setupUi

    def retranslateUi(self, suggestDialog):
        suggestDialog.setWindowTitle(QCoreApplication.translate("suggestDialog", u"Dialog", None))
        self.label_6.setText(QCoreApplication.translate("suggestDialog", u"Search for:", None))
        self.searchType.setItemText(0, QCoreApplication.translate("suggestDialog", u"N-grams and words", None))
        self.searchType.setItemText(1, QCoreApplication.translate("suggestDialog", u"N-grams only", None))
        self.searchType.setItemText(2, QCoreApplication.translate("suggestDialog", u"Words only", None))

        self.scowlSize.setItemText(0, "")
        self.scowlSize.setItemText(1, QCoreApplication.translate("suggestDialog", u"10", None))
        self.scowlSize.setItemText(2, QCoreApplication.translate("suggestDialog", u"20", None))
        self.scowlSize.setItemText(3, QCoreApplication.translate("suggestDialog", u"35", None))
        self.scowlSize.setItemText(4, QCoreApplication.translate("suggestDialog", u"40", None))
        self.scowlSize.setItemText(5, QCoreApplication.translate("suggestDialog", u"50", None))
        self.scowlSize.setItemText(6, QCoreApplication.translate("suggestDialog", u"55", None))
        self.scowlSize.setItemText(7, QCoreApplication.translate("suggestDialog", u"60", None))
        self.scowlSize.setItemText(8, QCoreApplication.translate("suggestDialog", u"70", None))
        self.scowlSize.setItemText(9, QCoreApplication.translate("suggestDialog", u"80", None))

#if QT_CONFIG(tooltip)
        self.scowlSize.setToolTip(QCoreApplication.translate("suggestDialog", u"Filter for words with size greater than selected in SCOWL. If blank, only filters common stopwords", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("suggestDialog", u"SCOWL size filter:", None))
#if QT_CONFIG(tooltip)
        self.minOccur.setToolTip(QCoreApplication.translate("suggestDialog", u"Word/n-gram must occur at least this many times", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("suggestDialog", u"Minimum occurrence:", None))
#if QT_CONFIG(tooltip)
        self.minNgram.setToolTip(QCoreApplication.translate("suggestDialog", u"N-gram must be this many words long", None))
#endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("suggestDialog", u"Min n-gram length:", None))
#if QT_CONFIG(tooltip)
        self.maxNgram.setToolTip(QCoreApplication.translate("suggestDialog", u"N-gram cannot be longer than this value", None))
#endif // QT_CONFIG(tooltip)
        self.label_7.setText(QCoreApplication.translate("suggestDialog", u"Max n-gram length:", None))
#if QT_CONFIG(tooltip)
        self.detect.setToolTip(QCoreApplication.translate("suggestDialog", u"Perform selected search", None))
#endif // QT_CONFIG(tooltip)
        self.detect.setText(QCoreApplication.translate("suggestDialog", u"Detect", None))
#if QT_CONFIG(tooltip)
        self.toDictionary.setToolTip(QCoreApplication.translate("suggestDialog", u"Send selected translation and outline to dictionary", None))
#endif // QT_CONFIG(tooltip)
        self.toDictionary.setText(QCoreApplication.translate("suggestDialog", u"To Dictionary", None))
    # retranslateUi

