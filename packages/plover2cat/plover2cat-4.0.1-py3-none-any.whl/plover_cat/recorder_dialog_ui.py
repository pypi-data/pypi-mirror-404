# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'recorder_dialog.ui'
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
    QDialogButtonBox, QFormLayout, QLabel, QSizePolicy,
    QSlider, QVBoxLayout, QWidget)

class Ui_recorderDialog(object):
    def setupUi(self, recorderDialog):
        if not recorderDialog.objectName():
            recorderDialog.setObjectName(u"recorderDialog")
        recorderDialog.resize(400, 261)
        self.verticalLayout = QVBoxLayout(recorderDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.audio_device = QComboBox(recorderDialog)
        self.audio_device.setObjectName(u"audio_device")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.audio_device)

        self.label_17 = QLabel(recorderDialog)
        self.label_17.setObjectName(u"label_17")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_17)

        self.audio_codec = QComboBox(recorderDialog)
        self.audio_codec.setObjectName(u"audio_codec")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.audio_codec)

        self.label_18 = QLabel(recorderDialog)
        self.label_18.setObjectName(u"label_18")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_18)

        self.audio_container = QComboBox(recorderDialog)
        self.audio_container.setObjectName(u"audio_container")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.audio_container)

        self.label_19 = QLabel(recorderDialog)
        self.label_19.setObjectName(u"label_19")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_19)

        self.audio_sample_rate = QComboBox(recorderDialog)
        self.audio_sample_rate.setObjectName(u"audio_sample_rate")
        self.audio_sample_rate.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.audio_sample_rate)

        self.label_20 = QLabel(recorderDialog)
        self.label_20.setObjectName(u"label_20")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_20)

        self.audio_channels = QComboBox(recorderDialog)
        self.audio_channels.setObjectName(u"audio_channels")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.audio_channels)

        self.label_16 = QLabel(recorderDialog)
        self.label_16.setObjectName(u"label_16")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_16)

        self.label_3 = QLabel(recorderDialog)
        self.label_3.setObjectName(u"label_3")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.audio_encoding = QComboBox(recorderDialog)
        self.audio_encoding.setObjectName(u"audio_encoding")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.audio_encoding)

        self.label = QLabel(recorderDialog)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.label)

        self.quality_slider = QSlider(recorderDialog)
        self.quality_slider.setObjectName(u"quality_slider")
        self.quality_slider.setMaximum(4)
        self.quality_slider.setValue(2)
        self.quality_slider.setOrientation(Qt.Orientation.Horizontal)

        self.formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.quality_slider)

        self.label_2 = QLabel(recorderDialog)
        self.label_2.setObjectName(u"label_2")

        self.formLayout.setWidget(7, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.audio_bitrate = QComboBox(recorderDialog)
        self.audio_bitrate.setObjectName(u"audio_bitrate")

        self.formLayout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.audio_bitrate)


        self.verticalLayout.addLayout(self.formLayout)

        self.buttonBox = QDialogButtonBox(recorderDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(recorderDialog)
        self.buttonBox.accepted.connect(recorderDialog.accept)
        self.buttonBox.rejected.connect(recorderDialog.reject)

        QMetaObject.connectSlotsByName(recorderDialog)
    # setupUi

    def retranslateUi(self, recorderDialog):
        recorderDialog.setWindowTitle(QCoreApplication.translate("recorderDialog", u"Dialog", None))
#if QT_CONFIG(tooltip)
        self.audio_device.setToolTip(QCoreApplication.translate("recorderDialog", u"Select where to receive audio input", None))
#endif // QT_CONFIG(tooltip)
        self.label_17.setText(QCoreApplication.translate("recorderDialog", u"Audio Codec:", None))
#if QT_CONFIG(tooltip)
        self.audio_codec.setToolTip(QCoreApplication.translate("recorderDialog", u"Select the audio codec to record with, depends on system codecs", None))
#endif // QT_CONFIG(tooltip)
        self.label_18.setText(QCoreApplication.translate("recorderDialog", u"File Container:", None))
#if QT_CONFIG(tooltip)
        self.audio_container.setToolTip(QCoreApplication.translate("recorderDialog", u"Select audio file type, depends on system", None))
#endif // QT_CONFIG(tooltip)
        self.label_19.setText(QCoreApplication.translate("recorderDialog", u"Sample Rate:", None))
#if QT_CONFIG(tooltip)
        self.audio_sample_rate.setToolTip(QCoreApplication.translate("recorderDialog", u"Select the sample rate for the recorded audio", None))
#endif // QT_CONFIG(tooltip)
        self.label_20.setText(QCoreApplication.translate("recorderDialog", u"Channels:", None))
#if QT_CONFIG(tooltip)
        self.audio_channels.setToolTip(QCoreApplication.translate("recorderDialog", u"Select number of channels to record from", None))
#endif // QT_CONFIG(tooltip)
        self.label_16.setText(QCoreApplication.translate("recorderDialog", u"Input Device:", None))
        self.label_3.setText(QCoreApplication.translate("recorderDialog", u"Encoding:", None))
        self.label.setText(QCoreApplication.translate("recorderDialog", u"Quality:", None))
#if QT_CONFIG(tooltip)
        self.quality_slider.setToolTip(QCoreApplication.translate("recorderDialog", u"Quality of audio recording, from very bad to very good", None))
#endif // QT_CONFIG(tooltip)
        self.label_2.setText(QCoreApplication.translate("recorderDialog", u"Bitrate:", None))
#if QT_CONFIG(tooltip)
        self.audio_bitrate.setToolTip(QCoreApplication.translate("recorderDialog", u"Select bitrate for recording", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

