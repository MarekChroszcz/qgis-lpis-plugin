# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SearchLPIS
                                 A QGIS plugin
 Wyszukiwarka działek LPIS
                             -------------------
        begin                : 2016-09-28
        copyright            : (C) 2016 by Sebastian Schulz / GIS Support
        email                : sebastian.schulz@gis-support.pl
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load SearchLPIS class from file SearchLPIS.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .search_lpis import SearchLPIS
    return SearchLPIS(iface)
