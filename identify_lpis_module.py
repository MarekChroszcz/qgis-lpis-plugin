# -*- coding: utf-8 -*-
"""
/***************************************************************************
IdentifyLPIS
                                 A QGIS plugin
 Identyfikacja działek LPIS
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
from PyQt4.QtCore import QSettings, QVariant
from qgis.gui import QgsMapToolEmitPoint, QgsMessageBar
from qgis.core import QgsGeometry, QgsPoint, QgsCoordinateTransform, \
    QgsCoordinateReferenceSystem, QgsMapLayerRegistry, QgsVectorLayer, \
    QgsField, QgsFeature
import urllib
import json
import processing


class IdentifyLPISModule(QgsMapToolEmitPoint):
    def __init__(self, parent):
        self.parent = parent
        self.iface = parent.iface
        self.canvas = parent.canvas
        super(QgsMapToolEmitPoint, self).__init__(self.canvas)
        self.canvasClicked.connect(self.findPlot)
        self.deactivated.connect(self.closeOnChangeTool)

    def closeOnChangeTool(self):
        self.parent.identifyTool.setChecked(False)

    def findPlot(self, point):
        trans = QgsCoordinateTransform(
            self.canvas.mapRenderer().destinationCrs(),
            QgsCoordinateReferenceSystem(2180))
        point = QgsGeometry.fromPoint(point)
        point.transform(trans)
        params = {
            'wkt': point.exportToWkt(),
            'key': QSettings().value('gissupport/api/key')
        }
        data = ''
        try:
            params = urllib.urlencode(params)
            r = urllib.urlopen('http://api.gis-support.pl/identify?' + params)
            if r.getcode() == 403:
                self.iface.messageBar().pushMessage(
                    u'Identyfikacja LPIS',
                    u'Nieprawidłowy klucz GIS Support',
                    level=QgsMessageBar.CRITICAL)
                return
            resp = json.loads(r.read())
            data = resp['data']
        except:
            data = 'app connection problem'
        if not data:
            self.iface.messageBar().pushMessage(
                u'Identyfikacja LPIS',
                u'Nie istnieją działki o podanych współrzędnych',
                level=QgsMessageBar.WARNING)
        elif data == 'db connection problem':
            self.iface.messageBar().pushMessage(
                u'Identyfikacja LPIS',
                u'Problem połączenia z bazą',
                level=QgsMessageBar.CRITICAL)
        elif data == 'app connection problem':
            self.iface.messageBar().pushMessage(
                u'Identyfikacja LPIS',
                u'Problem połączenia z aplikacją',
                level=QgsMessageBar.CRITICAL)
        else:
            self.createOutputLayer(resp)

    def createOutputLayer(self, resp):
        if not QgsMapLayerRegistry.instance().mapLayersByName(
                'Identyfikacja LPIS'):
            vl = QgsVectorLayer("MultiPolygon?crs=EPSG:2180",
                                "Identyfikacja LPIS",
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
            vl = processing.getObject('Identyfikacja LPIS')
            pr = vl.dataProvider()
            pr.addFeatures([feature])
        vl.updateExtents()
        vl.triggerRepaint()
        self.canvas.refresh()
        self.iface.messageBar().pushMessage(
                'Identyfikacja LPIS',
                u'Znaleziono działkę',
                level=QgsMessageBar.INFO)

    def toggleMapTool(self, state):
        if state:
            self.canvas.setMapTool(self)
        else:
            self.canvas.unsetMapTool(self)
