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
from PyQt4.QtCore import Qt, pyqtSignal
from qgis.gui import QgsMapToolEmitPoint


class IdentifyLPISModule(QgsMapToolEmitPoint):
    def __init__(self, parent):
        self.parent = parent
        self.iface = parent.iface
        self.canvas = parent.canvas
        super(QgsMapToolEmitPoint, self).__init__(self.canvas)
        self.canvasClicked.connect(self.findPlot)
        self.deactivated.connect(self.deactivate)

    def deactivate(self):
        self.parent.identifyTool.setChecked(False)
        super(IdentifyLPISModule, self).deactivate()

    def findPlot(self, coords):
        print coords

    def toggleMapTool(self, state):
        if state:
            self.canvas.setMapTool(self)
        else:
            self.canvas.unsetMapTool(self)
