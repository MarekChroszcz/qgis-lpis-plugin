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
from qgis.core import QgsFeature
from qgis.gui import QgsMapToolIdentify

class IdentifyLPISModule(QgsMapToolIdentify):
    def __init__(self, parent, parents=None):
        super(IdentifyLPISModule, self).__init__(parents)
        self.parent = parent
        self.iface = parent.iface
        print 'identify init'
