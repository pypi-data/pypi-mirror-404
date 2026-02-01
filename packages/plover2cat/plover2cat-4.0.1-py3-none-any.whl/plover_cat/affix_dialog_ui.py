# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'affix_dialog.ui'
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
    QDialogButtonBox, QFormLayout, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_affixDialog(object):
    def setupUi(self, affixDialog):
        if not affixDialog.objectName():
            affixDialog.setObjectName(u"affixDialog")
        affixDialog.resize(387, 173)
        self.verticalLayout = QVBoxLayout(affixDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(affixDialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.styleName = QComboBox(affixDialog)
        self.styleName.setObjectName(u"styleName")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.styleName)

        self.line = QFrame(affixDialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.line)

        self.label_3 = QLabel(affixDialog)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.prefixString = QLineEdit(affixDialog)
        self.prefixString.setObjectName(u"prefixString")
        self.prefixString.setClearButtonEnabled(False)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.prefixString)

        self.label_2 = QLabel(affixDialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.suffixString = QLineEdit(affixDialog)
        self.suffixString.setObjectName(u"suffixString")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.suffixString)


        self.verticalLayout.addLayout(self.formLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.insertTab = QPushButton(affixDialog)
        self.insertTab.setObjectName(u"insertTab")
        self.insertTab.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.horizontalLayout.addWidget(self.insertTab)

        self.saveAffixes = QPushButton(affixDialog)
        self.saveAffixes.setObjectName(u"saveAffixes")

        self.horizontalLayout.addWidget(self.saveAffixes)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.affixButtonBox = QDialogButtonBox(affixDialog)
        self.affixButtonBox.setObjectName(u"affixButtonBox")
        self.affixButtonBox.setOrientation(Qt.Orientation.Horizontal)
        self.affixButtonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.affixButtonBox)


        self.retranslateUi(affixDialog)
        self.affixButtonBox.accepted.connect(affixDialog.accept)
        self.affixButtonBox.rejected.connect(affixDialog.reject)

        QMetaObject.connectSlotsByName(affixDialog)
    # setupUi

    def retranslateUi(self, affixDialog):
        affixDialog.setWindowTitle(QCoreApplication.translate("affixDialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("affixDialog", u"Style:", None))
#if QT_CONFIG(tooltip)
        self.styleName.setToolTip(QCoreApplication.translate("affixDialog", u"Style to set affixes for", None))
#endif // QT_CONFIG(tooltip)
        self.label_3.setText(QCoreApplication.translate("affixDialog", u"Prefix string:", None))
#if QT_CONFIG(tooltip)
        self.prefixString.setToolTip(QCoreApplication.translate("affixDialog", u"String to add at start of paragraph", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("affixDialog", u"Suffix string:", None))
#if QT_CONFIG(tooltip)
        self.suffixString.setToolTip(QCoreApplication.translate("affixDialog", u"String to add to end of paragraph", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.insertTab.setToolTip(QCoreApplication.translate("affixDialog", u"Insert tab character into prefix/suffix string", None))
#endif // QT_CONFIG(tooltip)
        self.insertTab.setText(QCoreApplication.translate("affixDialog", u"Insert tab at cursor", None))
#if QT_CONFIG(tooltip)
        self.saveAffixes.setToolTip(QCoreApplication.translate("affixDialog", u"Save changes for selected style", None))
#endif // QT_CONFIG(tooltip)
        self.saveAffixes.setText(QCoreApplication.translate("affixDialog", u"Save", None))
    # retranslateUi

