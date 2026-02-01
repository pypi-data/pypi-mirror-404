# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'caption_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton,
    QSizePolicy, QSpinBox, QWidget)

class Ui_captionDialog(object):
    def setupUi(self, captionDialog):
        if not captionDialog.objectName():
            captionDialog.setObjectName(u"captionDialog")
        captionDialog.resize(555, 243)
        self.horizontalLayout_2 = QHBoxLayout(captionDialog)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.charOffset = QSpinBox(captionDialog)
        self.charOffset.setObjectName(u"charOffset")
        self.charOffset.setValue(5)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.charOffset)

        self.label = QLabel(captionDialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label)

        self.capLength = QSpinBox(captionDialog)
        self.capLength.setObjectName(u"capLength")
        self.capLength.setMinimum(1)
        self.capLength.setValue(32)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.capLength)

        self.maxDisplayLines = QSpinBox(captionDialog)
        self.maxDisplayLines.setObjectName(u"maxDisplayLines")
        self.maxDisplayLines.setMinimum(1)
        self.maxDisplayLines.setValue(3)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.maxDisplayLines)

        self.label_6 = QLabel(captionDialog)
        self.label_6.setObjectName(u"label_6")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.fontSelector = QPushButton(captionDialog)
        self.fontSelector.setObjectName(u"fontSelector")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.fontSelector)

        self.label_7 = QLabel(captionDialog)
        self.label_7.setObjectName(u"label_7")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_7)

        self.remoteCapHost = QComboBox(captionDialog)
        self.remoteCapHost.addItem("")
        self.remoteCapHost.addItem("")
        self.remoteCapHost.addItem("")
        self.remoteCapHost.addItem("")
        self.remoteCapHost.setObjectName(u"remoteCapHost")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.remoteCapHost)

        self.label_5 = QLabel(captionDialog)
        self.label_5.setObjectName(u"label_5")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.hostURL = QLineEdit(captionDialog)
        self.hostURL.setObjectName(u"hostURL")
        self.hostURL.setEnabled(False)

        self.formLayout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.hostURL)

        self.label_4 = QLabel(captionDialog)
        self.label_4.setObjectName(u"label_4")

        self.formLayout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.serverPort = QLineEdit(captionDialog)
        self.serverPort.setObjectName(u"serverPort")
        self.serverPort.setEnabled(False)

        self.formLayout.setWidget(8, QFormLayout.ItemRole.FieldRole, self.serverPort)

        self.label_2 = QLabel(captionDialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(8, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.serverPassword = QLineEdit(captionDialog)
        self.serverPassword.setObjectName(u"serverPassword")
        self.serverPassword.setEnabled(False)
        self.serverPassword.setEchoMode(QLineEdit.Password)

        self.formLayout.setWidget(9, QFormLayout.ItemRole.FieldRole, self.serverPassword)

        self.label_9 = QLabel(captionDialog)
        self.label_9.setObjectName(u"label_9")

        self.formLayout.setWidget(9, QFormLayout.ItemRole.LabelRole, self.label_9)

        self.enableTimeBuffer = QRadioButton(captionDialog)
        self.enableTimeBuffer.setObjectName(u"enableTimeBuffer")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.enableTimeBuffer)

        self.timeOffset = QSpinBox(captionDialog)
        self.timeOffset.setObjectName(u"timeOffset")
        self.timeOffset.setEnabled(True)
        self.timeOffset.setMaximum(100000)
        self.timeOffset.setSingleStep(1000)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.timeOffset)

        self.enableWordBuffer = QRadioButton(captionDialog)
        self.enableWordBuffer.setObjectName(u"enableWordBuffer")
        self.enableWordBuffer.setChecked(True)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.enableWordBuffer)

        self.label_3 = QLabel(captionDialog)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.rollCaptions = QCheckBox(captionDialog)
        self.rollCaptions.setObjectName(u"rollCaptions")
        self.rollCaptions.setChecked(True)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.rollCaptions)


        self.horizontalLayout_2.addLayout(self.formLayout)

        self.buttonBox = QDialogButtonBox(captionDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Vertical)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.horizontalLayout_2.addWidget(self.buttonBox)


        self.retranslateUi(captionDialog)
        self.buttonBox.accepted.connect(captionDialog.accept)
        self.buttonBox.rejected.connect(captionDialog.reject)

        QMetaObject.connectSlotsByName(captionDialog)
    # setupUi

    def retranslateUi(self, captionDialog):
        captionDialog.setWindowTitle(QCoreApplication.translate("captionDialog", u"Captioning Settings", None))
#if QT_CONFIG(tooltip)
        self.charOffset.setToolTip(QCoreApplication.translate("captionDialog", u"The \"buffer\" ", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("captionDialog", u"Maximum caption length:", None))
#if QT_CONFIG(tooltip)
        self.capLength.setToolTip(QCoreApplication.translate("captionDialog", u"Maximum number of characters in one line", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.maxDisplayLines.setToolTip(QCoreApplication.translate("captionDialog", u"Only display this number of lines in caption window", None))
#endif // QT_CONFIG(tooltip)
        self.label_6.setText(QCoreApplication.translate("captionDialog", u"Display max lines:", None))
#if QT_CONFIG(tooltip)
        self.fontSelector.setToolTip(QCoreApplication.translate("captionDialog", u"Font for display", None))
#endif // QT_CONFIG(tooltip)
        self.fontSelector.setText(QCoreApplication.translate("captionDialog", u"Choose Font", None))
        self.label_7.setText(QCoreApplication.translate("captionDialog", u"Display font:", None))
        self.remoteCapHost.setItemText(0, QCoreApplication.translate("captionDialog", u"None", None))
        self.remoteCapHost.setItemText(1, QCoreApplication.translate("captionDialog", u"Microsoft Teams", None))
        self.remoteCapHost.setItemText(2, QCoreApplication.translate("captionDialog", u"Zoom", None))
        self.remoteCapHost.setItemText(3, QCoreApplication.translate("captionDialog", u"OBS", None))

#if QT_CONFIG(tooltip)
        self.remoteCapHost.setToolTip(QCoreApplication.translate("captionDialog", u"Destination to send captions to", None))
#endif // QT_CONFIG(tooltip)
        self.label_5.setText(QCoreApplication.translate("captionDialog", u"Remote Endpoint:", None))
#if QT_CONFIG(tooltip)
        self.hostURL.setToolTip(QCoreApplication.translate("captionDialog", u"URL to send captions to", None))
#endif // QT_CONFIG(tooltip)
        self.label_4.setText(QCoreApplication.translate("captionDialog", u"Remote URL/Token:", None))
        self.label_2.setText(QCoreApplication.translate("captionDialog", u"Port:", None))
        self.label_9.setText(QCoreApplication.translate("captionDialog", u"Password:", None))
        self.enableTimeBuffer.setText(QCoreApplication.translate("captionDialog", u"Time Buffer:", None))
        self.timeOffset.setSuffix(QCoreApplication.translate("captionDialog", u"ms", None))
        self.enableWordBuffer.setText(QCoreApplication.translate("captionDialog", u"Word Buffer:", None))
        self.label_3.setText(QCoreApplication.translate("captionDialog", u"Roll Captions", None))
        self.rollCaptions.setText(QCoreApplication.translate("captionDialog", u"Yes (Default)", None))
    # retranslateUi

