# -*- coding: utf-8 -*-
_ = __import__(__package__.split(".", 1)[0])._

################################################################################
## Form generated from reading UI file 'config_plover_hid_widget.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QGridLayout, QLabel,
    QLineEdit, QSizePolicy, QWidget)

class Ui_PloverHidWidget(object):
    def setupUi(self, PloverHidWidget):
        if not PloverHidWidget.objectName():
            PloverHidWidget.setObjectName(u"PloverHidWidget")
        PloverHidWidget.resize(260, 140)
        PloverHidWidget.setWindowTitle(u"")
        self.gridLayout = QGridLayout(PloverHidWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.first_up_chord_send = QCheckBox(PloverHidWidget)
        self.first_up_chord_send.setObjectName(u"first_up_chord_send")

        self.gridLayout.addWidget(self.first_up_chord_send, 0, 0, 1, 2)

        self.double_tap_repeat = QCheckBox(PloverHidWidget)
        self.double_tap_repeat.setObjectName(u"double_tap_repeat")

        self.gridLayout.addWidget(self.double_tap_repeat, 1, 0, 1, 2)

        self.label_repeat_delay_ms = QLabel(PloverHidWidget)
        self.label_repeat_delay_ms.setObjectName(u"label_repeat_delay_ms")

        self.gridLayout.addWidget(self.label_repeat_delay_ms, 2, 0, 1, 1)

        self.repeat_delay_ms = QLineEdit(PloverHidWidget)
        self.repeat_delay_ms.setObjectName(u"repeat_delay_ms")

        self.gridLayout.addWidget(self.repeat_delay_ms, 2, 1, 1, 1)

        self.label_repeat_interval_ms = QLabel(PloverHidWidget)
        self.label_repeat_interval_ms.setObjectName(u"label_repeat_interval_ms")

        self.gridLayout.addWidget(self.label_repeat_interval_ms, 3, 0, 1, 1)

        self.repeat_interval_ms = QLineEdit(PloverHidWidget)
        self.repeat_interval_ms.setObjectName(u"repeat_interval_ms")

        self.gridLayout.addWidget(self.repeat_interval_ms, 3, 1, 1, 1)

        self.label_device_scan_interval_ms = QLabel(PloverHidWidget)
        self.label_device_scan_interval_ms.setObjectName(u"label_device_scan_interval_ms")

        self.gridLayout.addWidget(self.label_device_scan_interval_ms, 4, 0, 1, 1)

        self.device_scan_interval_ms = QLineEdit(PloverHidWidget)
        self.device_scan_interval_ms.setObjectName(u"device_scan_interval_ms")

        self.gridLayout.addWidget(self.device_scan_interval_ms, 4, 1, 1, 1)

#if QT_CONFIG(shortcut)
        self.label_repeat_delay_ms.setBuddy(self.repeat_delay_ms)
        self.label_repeat_interval_ms.setBuddy(self.repeat_interval_ms)
        self.label_device_scan_interval_ms.setBuddy(self.device_scan_interval_ms)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(PloverHidWidget)
        self.first_up_chord_send.clicked["bool"].connect(PloverHidWidget.update_first_up_chord_send)
        self.double_tap_repeat.clicked["bool"].connect(PloverHidWidget.update_double_tap_repeat)
        self.repeat_delay_ms.textChanged.connect(PloverHidWidget.update_repeat_delay_ms)
        self.repeat_interval_ms.textChanged.connect(PloverHidWidget.update_repeat_interval_ms)
        self.device_scan_interval_ms.textChanged.connect(PloverHidWidget.update_device_scan_interval_ms)

        QMetaObject.connectSlotsByName(PloverHidWidget)
    # setupUi

    def retranslateUi(self, PloverHidWidget):
#if QT_CONFIG(tooltip)
        self.first_up_chord_send.setToolTip(QCoreApplication.translate("PloverHidWidget", u"When the first key in a chord is released, the chord is sent.\n"
"If the key is pressed and released again, another chord is sent.", None))
#endif // QT_CONFIG(tooltip)
        self.first_up_chord_send.setText(QCoreApplication.translate("PloverHidWidget", u"Send chord on first key release", None))
#if QT_CONFIG(tooltip)
        self.double_tap_repeat.setToolTip(QCoreApplication.translate("PloverHidWidget", u"Tap and then hold a chord to send it repeatedly.", None))
#endif // QT_CONFIG(tooltip)
        self.double_tap_repeat.setText(QCoreApplication.translate("PloverHidWidget", u"Double tap to repeat", None))
        self.label_repeat_delay_ms.setText(QCoreApplication.translate("PloverHidWidget", u"Repeat delay (ms)", None))
#if QT_CONFIG(tooltip)
        self.repeat_delay_ms.setToolTip(QCoreApplication.translate("PloverHidWidget", u"Delay before chord starts repeating.", None))
#endif // QT_CONFIG(tooltip)
        self.label_repeat_interval_ms.setText(QCoreApplication.translate("PloverHidWidget", u"Repeat interval (ms)", None))
#if QT_CONFIG(tooltip)
        self.repeat_interval_ms.setToolTip(QCoreApplication.translate("PloverHidWidget", u"Interval between chord repetitions.", None))
#endif // QT_CONFIG(tooltip)
        self.label_device_scan_interval_ms.setText(QCoreApplication.translate("PloverHidWidget", u"Device scan interval (ms)", None))
#if QT_CONFIG(tooltip)
        self.device_scan_interval_ms.setToolTip(QCoreApplication.translate("PloverHidWidget", u"How often to scan for newly plugged-in devices.", None))
#endif // QT_CONFIG(tooltip)
        pass
    # retranslateUi

