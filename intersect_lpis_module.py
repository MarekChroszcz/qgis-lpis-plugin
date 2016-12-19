# -*- coding: utf-8 -*-
"""
/***************************************************************************
 IntersectLPISDialog
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
from PyQt4.QtCore import QSettings, QVariant
from PyQt4.QtGui import QDialog
import os.path
import urllib
import json
import processing
from qgis.core import QgsMapLayer, QgsMapLayerRegistry, QgsGeometry, \
        QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsVectorLayer, \
        QgsFeature, QgsField, QgsRasterLayer
from qgis.gui import QgsMessageBar, QgsMapLayerComboBox

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'intersect_lpis_module.ui'))


class IntersectLPISModule(QDialog, FORM_CLASS):
    def __init__(self, parent, parents=None):
        """Constructor."""
        super(IntersectLPISModule, self).__init__(parents)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.parent = parent
        self.iface = parent.iface
        self.keyLineEdit.setText(QSettings().value('gissupport/api/key'))
        self.saveKeyButton.clicked.connect(self.saveKey)
        self.addWMSButton.clicked.connect(self.addWMS)
        self.layerComboBox.setFocus()

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

    def saveKey(self):
        QSettings().setValue('gissupport/api/key',
                             self.keyLineEdit.text())

    def createOutputLayer(self, resp):
        if not QgsMapLayerRegistry.instance().mapLayersByName(
                'Przeciecia LPIS'):
            vl = QgsVectorLayer("MultiPolygon?crs=EPSG:2180",
                                "Przeciecia LPIS",
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
        for wkt in resp['data']:
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromWkt(wkt[0]))
            feature.setAttributes([a for a in wkt[1:]])
            vl = processing.getObject('Przeciecia LPIS')
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
        if resp['status'] == 'limited':
            self.iface.messageBar().pushMessage(
                'Przeciecia LPIS',
                u'Wynik został ograniczony do %d działek \
                ze względu na ograniczenia serwera' % len(resp['data']),
                level=QgsMessageBar.WARNING)
        else:
            self.iface.messageBar().pushMessage(
                'Przeciecia LPIS',
                u'Liczba działek przeciętych \
                przez warstwę: %d' % len(resp['data']),
                level=QgsMessageBar.INFO)

    def findPlots(self):
        vl = self.layerComboBox.currentLayer()
        egeom = QgsGeometry.fromWkt('GEOMETRYCOLLECTION()')
        geom = egeom
        trans = QgsCoordinateTransform(vl.crs(),
                                       QgsCoordinateReferenceSystem(2180))
        if not self.selectCheckBox.isChecked():
            for f in vl.getFeatures():
                f.geometry().transform(trans)
                geom = geom.combine(f.geometry())
            if geom.exportToWkt() == egeom:
                self.iface.messageBar().pushMessage(
                    'Przeciecia LPIS',
                    u'Brak obiektów na warstwie',
                    level=QgsMessageBar.WARNING)
                return False
        else:
            for f in vl.selectedFeatures():
                f.geometry().transform(trans)
                geom = geom.combine(f.geometry())
            if geom.exportToWkt() == egeom:
                self.iface.messageBar().pushMessage(
                    'Przeciecia LPIS',
                    u'Brak zaznaczonych obiektów',
                    level=QgsMessageBar.WARNING)
                return False
        params = {
            'wkt': geom.exportToWkt(),
            'key': self.keyLineEdit.text().encode('utf-8').strip()
        }
        data = ''
        try:
            r = urllib.urlopen(
                'http://api.gis-support.pl/intersect?key=' + params['key'],
                json.dumps(params))
            if r.getcode() == 403:
                self.iface.messageBar().pushMessage(
                    u'Przecięcia LPIS',
                    u'Nieprawidłowy klucz GIS Support',
                    level=QgsMessageBar.CRITICAL)
                return False
            resp = json.loads(r.read())
            data = resp['data']
        except:
            data = 'app connection problem'
        if not data:
            self.iface.messageBar().pushMessage(
                u'Przecięcia LPIS',
                u'Warstwa nie przecina żadnej działki',
                level=QgsMessageBar.WARNING)
        elif data == 'db connection problem':
            self.iface.messageBar().pushMessage(
                u'Przecięcia LPIS',
                u'Problem połączenia z bazą',
                level=QgsMessageBar.CRITICAL)
        elif data == 'app connection problem':
            self.iface.messageBar().pushMessage(
                u'Przecięcia LPIS',
                u'Problem połączenia z aplikacją',
                level=QgsMessageBar.CRITICAL)
        else:
            self.createOutputLayer(resp)
            return True
        return False

    def accept(self):
        if not self.layerComboBox.currentLayer():
            self.iface.messageBar().pushMessage(
                u'Przecięcia LPIS',
                u'Podaj warstwę do przecięcia',
                level=QgsMessageBar.WARNING)
        elif self.findPlots():
            super(IntersectLPISModule, self).accept()
