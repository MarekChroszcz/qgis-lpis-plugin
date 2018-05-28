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
from future import standard_library
standard_library.install_aliases()
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QSettings, QVariant, Qt
from qgis.PyQt.QtWidgets import QMessageBox, QWidget, QDialog
from qgis.PyQt.QtGui import QPixmap
import os.path
import locale
import pickle
from functools import cmp_to_key
import urllib.request, urllib.parse, urllib.error
import json
from qgis.core import QgsFeature, QgsGeometry, QgsVectorLayer, \
    QgsProject, QgsRasterLayer, QgsField, QgsCoordinateTransform, Qgis

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
                                     'rb'))
        #print(self.data)
        self.w = sorted(list(self.data.keys()), key=cmp_to_key(locale.strcoll))
        self.wComboBox.addItems(self.w)
        index = self.wComboBox.findText(
            QSettings().value('gissupport/search_lpis/w'),
            Qt.MatchFixedString)
        if index >= 0:
            self.wComboBox.setCurrentIndex(index)
        self.p = sorted(list(self.data
                        [self.wComboBox.currentText()].keys()),
                        key=cmp_to_key(locale.strcoll))
        self.pComboBox.addItems(self.p)
        index = self.pComboBox.findText(
            QSettings().value('gissupport/search_lpis/p'),
            Qt.MatchFixedString)
        if index >= 0:
            self.pComboBox.setCurrentIndex(index)
        self.g = sorted(self.data
                        [self.wComboBox.currentText()]
                        [self.pComboBox.currentText()],
                        key=cmp_to_key(locale.strcoll))
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
                        key=cmp_to_key(locale.strcoll))
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
        self.skipO.stateChanged.connect(self.toggleO)
        self.keyLineEdit.setText(QSettings().value('gissupport/api/key'))
        self.saveKeyButton.clicked.connect(self.saveKey)
        self.addWMSButton.clicked.connect(self.addWMS)
        self.nLineEdit.setFocus()
        self.label_9.setPixmap(QPixmap(':/plugins/SearchLPIS/info.png'))

    def saveKey(self):
        QSettings().setValue('gissupport/api/key',
                             self.keyLineEdit.text())

    def saveO(self):
        QSettings().setValue('gissupport/search_lpis/o',
                             self.oComboBox.currentText())

    def toggleO(self):
        if self.skipO.isChecked():
            self.oComboBox.setEnabled(False)
        else:
            self.oComboBox.setEnabled(True)

    def addWMS(self):
        if not QgsProject.instance().mapLayersByName(
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
            QgsProject.instance().addMapLayer(layer)
        else:
            pass

    def findPlot(self):
        params = {
            'w': self.wComboBox.currentText(),
            'p': self.pComboBox.currentText(),
            'g': self.gComboBox.currentText(),
            'n': self.nLineEdit.text(),
            'key': self.keyLineEdit.text().strip()
        }
        if not self.skipO.isChecked():
            params['o'] = self.oComboBox.currentText()
        data = ''
        try:
            r = urllib.request.urlopen('http://api.gis-support.pl/lpis?' + urllib.parse.urlencode(params))
            if r.getcode() == 403:
                self.iface.messageBar().pushMessage(
                    'Wyszukiwarka LPIS',
                    u'Nieprawidłowy klucz GIS Support',
                    level=Qgis.Critical)
                return False
            data = json.loads(r.read().decode())['data']
        except:
            data = 'app connection problem'
        if data:
            if data == 'db connection problem':
                self.iface.messageBar().pushMessage(
                    'Wyszukiwarka LPIS',
                    u'Problem połączenia z bazą',
                    level=Qgis.Critical)
                return False
            elif data == 'app connection problem':
                self.iface.messageBar().pushMessage(
                    'Wyszukiwarka LPIS',
                    u'Problem połączenia z aplikacją',
                    level=Qgis.Critical)
                return False
            else:
                if not QgsProject.instance().mapLayersByName(
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
                    QgsProject.instance().addMapLayer(vl)
                vl = QgsProject.instance().mapLayersByName(
                    'Wyszukiwarka LPIS')[0]
                pr = vl.dataProvider()
                for wkt in data:
                    feature = QgsFeature()
                    feature.setGeometry(QgsGeometry.fromWkt(wkt[0]))
                    feature.setAttributes([a for a in wkt[1:]])
                    pr.addFeatures([feature])
                vl.updateExtents()
                self.iface.mapCanvas().setExtent(
                    QgsCoordinateTransform(
                        vl.crs(),
                        self.iface.
                        mapCanvas().
                        mapSettings().
                        destinationCrs(),
                        QgsProject.instance()).
                    transform(vl.extent()))
                self.iface.mapCanvas().refresh()
                notfound_parcels = []
                for nr in params['n'].replace(" ","").split(','):
                    if nr not in vl.uniqueValues(vl.fields().indexFromName('numer')):
                        notfound_parcels.append(nr)
                if notfound_parcels:
                    self.iface.messageBar().pushMessage(
                        'Wyszukiwarka LPIS',
                        u"Nie znaleziono działek o numerze: {}".format(','.join(notfound_parcels)),
                        level=Qgis.Info)
                if len(data) > 1 and ',' not in params['n']:
                    self.iface.messageBar().pushMessage(
                        'Wyszukiwarka LPIS',
                        u'Istnieje więcej działek o podanym numerze',
                        level=Qgis.Info)
                return True
        else:
            self.iface.messageBar().pushMessage(
                'Wyszukiwarka LPIS',
                u'Nie znaleziono działki',
                level=Qgis.Warning)
            return False

    def updateP(self):
        self.pComboBox.clear()
        self.p = sorted(list(self.data
                        [self.wComboBox.currentText()].keys()),
                        key=cmp_to_key(locale.strcoll))
        self.pComboBox.addItems(self.p)
        QSettings().setValue('gissupport/search_lpis/w',
                             self.wComboBox.currentText())

    def updateG(self):
        self.gComboBox.clear()
        if self.pComboBox.currentText():
            self.g = sorted(self.data
                            [self.wComboBox.currentText()]
                            [self.pComboBox.currentText()],
                            key=cmp_to_key(locale.strcoll))
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
                level=Qgis.Warning)
        elif not self.keyLineEdit.text():
            self.iface.messageBar().pushMessage(
                'Wyszukiwarka LPIS',
                u'Podaj klucz GIS Support',
                level=Qgis.Warning)
        elif self.findPlot():
            super(SearchLPISModule, self).accept()
