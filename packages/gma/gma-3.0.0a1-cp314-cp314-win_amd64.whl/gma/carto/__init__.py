# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
import matplotlib.markers as mk 
import matplotlib.collections as clt
import matplotlib.axes as axes
import matplotlib.cbook as cbook
import matplotlib.path as mpath
import matplotlib.transforms as mtransforms
import matplotlib.patches as ptc
import matplotlib.colors as cor
import matplotlib.font_manager as ftm
import matplotlib.textpath as tph

import pandas as pd
from .._algos.core import tools, env, dtypes, error, np, env, GMA_Data
from .._algos.core.gdata import const
from .._algos.geo.srs import (CoordinateReferenceSystem, CoordinateTransformation, 
                              create_bou, create_ext, MapBoundary, UNIT_DEG_X, UNIT_DEG_Y)

from .._algos.arrmt import to_numeric_array

from .._algos.geo.geometry import Geometry, base_geom_to_points
from .._algos.geo.layer import Layer
from .._algos.geo.feature import Feature
from .._algos.geo.dataset import Dataset, raster_translate, mask_array_nodata
from .._algos.geo.geodatabase import open_file, open_raster
from .._algos.spmis.meatran import Miscellaneous

def polygon_list_to_points(geoms, ndim = 2, node = False):
    '''获取基本多边形列表的所有点'''
    points = []
    for geom in geoms:
        for sub_geom in geom:
            pts = base_geom_to_points(sub_geom, ndim)
            points.append(pts)

    if node:
        ps_len = np.array([len(ps) for ps in points])
        geom_p_len = np.cumsum(ps_len)
        ps_len_sum = ps_len.sum()

        codes = np.full(ps_len_sum, 2)
        codes[geom_p_len - 1] = 79
        codes[geom_p_len - ps_len] = 1 

        points = np.concatenate(points)
        return points, codes
    else:
        return points
    
def line_list_to_points(geoms, ndim = 2, node = False):
    '''获取基本线列表的所有点'''

    points = []
    for geom in geoms:
        pts = base_geom_to_points(geom, ndim)
        points.append(pts)

    if node:
        ps_len = np.array([len(ps) for ps in points])
        geom_p_len = np.cumsum(ps_len)
        ps_len_sum = ps_len.sum()

        codes = np.full(ps_len_sum, 2)
        codes[geom_p_len - ps_len] = 1

        points = np.concatenate(points)
        return points, codes
    else:
        return points

def point_list_to_points(geoms, ndim = 2, node = False):
    '''获取基本点列表的所有点'''
    points = []
    for geom in geoms:
        pts = base_geom_to_points(geom, ndim)
        points.append(pts)

    if node:
        ps_len = np.array([len(ps) for ps in points])
        ps_len_sum = ps_len.sum()
        codes = np.full(ps_len_sum, 1)
        points = np.concatenate(points)
        return points, codes
    else:
        return points
    
class GeoAxes(axes.Axes):

    name = 'geo_axes'

    def __init__(self, *args, **kwargs):
        # 调用父类初始化
        super().__init__(*args, **kwargs)

import matplotlib.projections as proj
proj.register_projection(GeoAxes)
