# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SearchLPISDialog
                                 A QGIS plugin
 Wyszukiwarka działek LPIS
                             -------------------
        begin                : 2016-09-28
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Sebastian Schulz / GIS Support
        email                : sebastian.schulz@gis-support.pl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4 import uic
from PyQt4.QtCore import QSettings, QVariant, Qt
from PyQt4.QtGui import QMessageBox, QWidget, QDialog
import os.path
import locale
import pickle
import urllib
import json
import processing
from qgis.core import QgsFeature, QgsGeometry, QgsVectorLayer, \
    QgsMapLayerRegistry, QgsRasterLayer, QgsField, QgsCoordinateTransform
from qgis.gui import QgsMessageBar

locale.setlocale(locale.LC_ALL, '')
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'search_lpis_module.ui'))


class SearchLPISModule(QDialog, FORM_CLASS):
    def __init__(self, parent, parents=None):
        """Constructor."""
        super(SearchLPISModule, self).__init__(parents)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.parent = parent
        self.iface = parent.iface
        self.data = pickle.load(open(os.path.dirname(__file__) +
                                     '/options.pkl',
                                     'r'))
        self.w = sorted(self.data.keys(), cmp=locale.strcoll)
        self.wComboBox.addItems(self.w)
        index = self.wComboBox.findText(
            QSettings().value('gissupport/search_lpis/w'),
            Qt.MatchFixedString)
        if index >= 0:
            self.wComboBox.setCurrentIndex(index)
        self.p = sorted(self.data
                        [self.wComboBox.currentText()].keys(),
                        cmp=locale.strcoll)
        self.pComboBox.addItems(self.p)
        index = self.pComboBox.findText(
            QSettings().value('gissupport/search_lpis/p'),
            Qt.MatchFixedString)
        if index >= 0:
            self.pComboBox.setCurrentIndex(index)
        self.g = sorted(self.data
                        [self.wComboBox.currentText()]
                        [self.pComboBox.currentText()],
                        cmp=locale.strcoll)
        self.gComboBox.addItems(self.g)
        index = self.gComboBox.findText(
            QSettings().value('gissupport/search_lpis/g'),
            Qt.MatchFixedString)
        if index >= 0:
            self.gComboBox.setCurrentIndex(index)
        self.o = sorted(self.data
                        [self.wComboBox.currentText()]
                        [self.pComboBox.currentText()]
                        [self.gComboBox.currentText()],
                        cmp=locale.strcoll)
        self.oComboBox.addItems(self.o)
        index = self.oComboBox.findText(
            QSettings().value('gissupport/search_lpis/o'),
            Qt.MatchFixedString)
        if index >= 0:
            self.oComboBox.setCurrentIndex(index)
        self.wComboBox.currentIndexChanged.connect(self.updateP)
        self.pComboBox.currentIndexChanged.connect(self.updateG)
        self.gComboBox.currentIndexChanged.connect(self.updateO)
        self.oComboBox.currentIndexChanged.connect(self.saveO)
        self.keyLineEdit.setText(QSettings().value('gissupport/api/key'))
        self.saveKeyButton.clicked.connect(self.saveKey)
        self.addWMSButton.clicked.connect(self.addWMS)
        self.nLineEdit.setFocus()

    def saveKey(self):
        QSettings().setValue('gissupport/api/key',
                             self.keyLineEdit.text())

    def saveO(self):
        QSettings().setValue('gissupport/search_lpis/o',
                             self.oComboBox.currentText())

    def addWMS(self):
        if not QgsMapLayerRegistry.instance().mapLayersByName(
                'Dzialki LPIS'):
            url = ("contextualWMSLegend=0&"
                   "crs=EPSG:2180&"
                   "dpiMode=7&"
                   "featureCount=10&"
                   "format=image/png8&"
                   "layers=NumeryDzialek&layers=Dzialki&"
                   "styles=&styles=&"
                   "url=http://mapy.geoportal.gov.pl"
                   "/wss/service/pub/guest/G2_GO_WMS/MapServer/WMSServer")
            layer = QgsRasterLayer(url, 'Dzialki LPIS', 'wms')
            QgsMapLayerRegistry.instance().addMapLayer(layer)
        else:
            pass

    def findPlot(self):
        params = {
            'w': self.wComboBox.currentText().encode('utf-8'),
            'p': self.pComboBox.currentText().encode('utf-8'),
            'g': self.gComboBox.currentText().encode('utf-8'),
            'o': self.oComboBox.currentText().encode('utf-8'),
            'n': self.nLineEdit.text().encode('utf-8'),
            'key': self.keyLineEdit.text().encode('utf-8').strip()
        }
        data = ''
        try:
            params = urllib.urlencode(params)
            r = urllib.urlopen('http://qgisapi.apps.divi.pl/lpis?' + params)
            if r.getcode() == 403:
                self.iface.messageBar().pushMessage(
                    'Wyszukiwarka LPIS',
                    u'Nieprawidłowy klucz GIS Support',
                    level=QgsMessageBar.CRITICAL)
                return False
            data = json.loads(r.read())['data']
        except:
            data = 'app connection problem'
        if data:
            if data == 'db connection problem':
                self.iface.messageBar().pushMessage(
                    'Wyszukiwarka LPIS',
                    u'Problem połączenia z bazą',
                    level=QgsMessageBar.CRITICAL)
                return False
            elif data == 'app connection problem':
                self.iface.messageBar().pushMessage(
                    'Wyszukiwarka LPIS',
                    u'Problem połączenia z aplikacją',
                    level=QgsMessageBar.CRITICAL)
                return False
            else:
                if not QgsMapLayerRegistry.instance().mapLayersByName(
                        'Wyszukiwarka LPIS'):
                    vl = QgsVectorLayer("MultiPolygon?crs=EPSG:2180",
                                        "Wyszukiwarka LPIS",
                                        "memory")
                    pr = vl.dataProvider()
                    vl.startEditing()
                    pr.addAttributes(
                        [QgsField("id", QVariant.String),
                         QgsField("objectid", QVariant.String),
                         QgsField("identyfika", QVariant.String),
                         QgsField("powierzchn", QVariant.String),
                         QgsField("teryt", QVariant.String),
                         QgsField("numer", QVariant.String),
                         QgsField("obreb", QVariant.String),
                         QgsField("wojewodztw", QVariant.String),
                         QgsField("powiat", QVariant.String),
                         QgsField("gmina", QVariant.String),
                         QgsField("data_od", QVariant.String),
                         QgsField("shape_leng", QVariant.String),
                         QgsField("shape_area", QVariant.String)])
                    vl.commitChanges()
                    QgsMapLayerRegistry.instance().addMapLayer(vl)
                for wkt in data:
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromWkt(wkt[0]))
                    feature.setAttributes([a for a in wkt[1:]])
                    vl = processing.getObject('Wyszukiwarka LPIS')
                    pr = vl.dataProvider()
                    pr.addFeatures([feature])
                vl.updateExtents()
                self.iface.mapCanvas().setExtent(
                    QgsCoordinateTransform(
                        vl.crs(),
                        self.iface.
                        mapCanvas().
                        mapRenderer().
                        destinationCrs()).
                    transform(vl.extent()))
                self.iface.mapCanvas().refresh()
                if len(data) > 1:
                    self.iface.messageBar().pushMessage(
                        'Wyszukiwarka LPIS',
                        u'Istnieje więcej działek o podanym numerze',
                        level=QgsMessageBar.INFO)
                return True
        else:
            self.iface.messageBar().pushMessage(
                'Wyszukiwarka LPIS',
                u'Nie znaleziono działki',
                level=QgsMessageBar.WARNING)
            return False

    def updateP(self):
        self.pComboBox.clear()
        self.p = sorted(self.data
                        [self.wComboBox.currentText()].keys(),
                        cmp=locale.strcoll)
        self.pComboBox.addItems(self.p)
        QSettings().setValue('gissupport/search_lpis/w',
                             self.wComboBox.currentText())

    def updateG(self):
        self.gComboBox.clear()
        if self.pComboBox.currentText():
            self.g = sorted(self.data
                            [self.wComboBox.currentText()]
                            [self.pComboBox.currentText()],
                            cmp=locale.strcoll)
            self.gComboBox.addItems(self.g)
            QSettings().setValue('gissupport/search_lpis/p',
                                 self.pComboBox.currentText())

    def updateO(self):
        self.oComboBox.clear()
        if self.gComboBox.currentText():
            self.o = sorted(self.data
                            [self.wComboBox.currentText()]
                            [self.pComboBox.currentText()]
                            [self.gComboBox.currentText()])
            self.oComboBox.addItems(self.o)
            QSettings().setValue('gissupport/search_lpis/g',
                                 self.gComboBox.currentText())

    def accept(self):
        if not self.nLineEdit.text():
            self.iface.messageBar().pushMessage(
                'Wyszukiwarka LPIS',
                u'Podaj numer działki',
                level=QgsMessageBar.WARNING)
        elif not self.keyLineEdit.text():
            self.iface.messageBar().pushMessage(
                'Wyszukiwarka LPIS',
                u'Podaj klucz GIS Support',
                level=QgsMessageBar.WARNING)
        elif self.findPlot():
            super(SearchLPISModule, self).accept()
