# -*- coding: utf-8 -*-
from .extlib import _gdal, _gdal_array, _ogr, _osr

from ..core import (os, np, json, io, os, re, xet, sqlite3, glob, warnings, GMA_Data, 
                     tools, error, gdata, dtypes, env)

from ..core.tools import init_data
dataset_io_numpy = lambda *args, **kwargs:call_gdal_fun(_gdal_array.DatasetIONumPy, *args, **kwargs)
band_io_numpy = lambda *args, **kwargs:call_gdal_fun(_gdal_array.BandRasterIONumPy, *args, **kwargs)

open_numpy_array = lambda *args, **kwargs:call_gdal_fun(_gdal_array.OpenNumPyArray, *args, **kwargs)
polygonize = lambda *args, **kwargs:call_gdal_fun(_gdal.FPolygonize, *args, **kwargs)
rasterize = lambda *args, **kwargs:call_gdal_fun(_gdal.RasterizeLayer, *args, **kwargs)
build_overviews = lambda *args, **kwargs:call_gdal_fun(_gdal.Dataset_BuildOverviews, *args, **kwargs)
contour_generate = lambda *args, **kwargs:call_gdal_fun(_gdal.ContourGenerate, *args, **kwargs)

file_from_mem_buffer = lambda *args, **kwargs:call_gdal_fun(_gdal.FileFromMemBuffer, *args, **kwargs)

term_progress = _gdal.TermProgress_nocb
un_link = _gdal.Unlink

get_driver_by_name = _gdal.GetDriverByName

get_last_error_msg = _gdal.GetLastErrorMsg
get_last_error_code = _gdal.GetLastErrorType
error_reset = _gdal.ErrorReset

def create_bou(left, bottom, right, top):

    bou = np.linspace([[left, top], [left, bottom], [right, bottom], [right, top]], 
                      [[left, bottom], [right, bottom], [right, top], [left, top]], 
                      env.IntPointNumber, 
                      endpoint = False, axis = 1)
    
    bou = np.concatenate(bou).round(4).tolist()
    bou.append(bou[0])

    return bou
    
def list_dir(in_path, recursive = False, **kwargs):

    if os.path.isfile(in_path):
        return [in_path]
    
    if '/vis' == in_path[:4].lower():
        if recursive:
            items = _gdal.ReadDirRecursive(in_path, **kwargs)
        else:
            items = _gdal.ReadDir(in_path)  
        if not items:
            items = []
        else:
            items = [f'{in_path}/{it}' for it in items[2:]]
    else:
        if recursive:
            items = glob.glob(f'{in_path}/**/*', recursive = True)
        else:
            items = glob.glob(f'{in_path}/*')      

    return items

def vsi_read(virtual_csv_path, mode = 'r'):
    # 以读取的方式打开虚拟文件
    virtual_csv_file = _gdal.VSIFOpenL(virtual_csv_path, mode)
    _gdal.VSIFSeekL(virtual_csv_file, 0, 2)  # 将文件指针移动到文件末尾
    file_size = _gdal.VSIFTellL(virtual_csv_file)  # 获取当前文件指针位置
    _gdal.VSIFSeekL(virtual_csv_file, 0, 0)  # 将文件指针移动到文件开头

    atio = _gdal.VSIFReadL(1, file_size, virtual_csv_file)
    _gdal.VSIFCloseL(virtual_csv_file)
    
    return atio

def get_xy_resolution(res):

    res_xy = tools.resize_items(res, 2)
    for r in res_xy:
        if not isinstance(r, (int, float)):
            raise ValueError(f'Incorrect resolution:{res}!')
    return res_xy

def open_ex(in_src, flags = 0, allowed_drivers = [], open_options = [], sibling_files = []):
    bds = call_gdal_fun(_gdal.OpenEx, in_src, flags, allowed_drivers, open_options, sibling_files)
    if bds is not None:
        return bds
    raise error.GMAError(f'Unable to open {in_src}!')

geom_error_info = {1:'Insufficient data to construct or process geometry.', # 'NOT_ENOUGH_DATA', 
                   2:'Memory allocation failed during geometry operation.', # 'NOT_ENOUGH_MEMORY',
                   3:'Specified geometry type is not supported.', # 'UNSUPPORTED_GEOMETRY_TYPE',
                   4:'Requested operation is invalid for this geometry.', # 'UNSUPPORTED_OPERATION',
                   5:'Geometry data is corrupted or malformed.', # 'CORRUPT_DATA',
                   6:'General operation failure without specific error code.', # 'FAILURE',
                   7:'Spatial reference system is not supported.', # 'UNSUPPORTED_SRS',
                   8:'Invalid geometry or feature handle.', # 'INVALID_HANDLE',
                   9:'Referenced feature does not exist.', # 'NON_EXISTING_FEATURE'
                   }

vector_tranlate_info = {2:'The operation completed, but there were non-critical issues.', 
                        3:'The operation failed to complete successfully.', 
                        4:'The operation failed and cannot be recovered (most severe).'
                   }

#############################################################################################

def call_gdal_fun(fun, *args, **kwargs):
    error_reset()
    try:
        res = fun(*args, **kwargs)
    except Exception as e:
        e = str(e)
        if 'in method' in e:
            er_args = e.split(",")[-1].split('of')[0].strip()
            raise error.TranslateError(f"An error occurred during translating({er_args} error)!") from None
        raise error.TranslateError(e) from None
    
    er = get_last_error_msg()
    code = get_last_error_code()
    error_reset()

    if code in (3, 4):  # 处理错误
        raise error.TranslateError(er)

    if env.UseGDALWarnings:
        if er:
            warnings.warn(er) 

    return res

CHARACTERS = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

############################################## 随机名称
def randint_name(size = 6): 

    # 随机选择6个字符
    random_chars = np.random.choice(CHARACTERS, size = size)
    # 将结果转换为字符串
    result = ''.join(random_chars)
    
    return result

def mem_temp_path(ext = ''):
    '''Temp layer file path in work space. -> str'''
    if not ext.startswith('.'):
        ext = f'.{ext}'
    return f'{env.WorkSpace}/{randint_name()}{ext}'

####################### jupyter 用
def get_sel(count_x, max_l):
    if count_x > max_l:
        l = max_l
        half_of_max = max_l // 2
        sels0 = (0, half_of_max)
        if max_l % 2 == 0:
            sels2 = (count_x - half_of_max + 1, count_x)
        else:
            sels2 = (count_x - half_of_max, count_x)
        sels = [sels0, sels2]
    else:
        l = count_x
        sels = [(0, count_x), (0, 0)]
    return sels, l 

def get_sel_from_list(sel_range, all_sel):
    sel = all_sel[slice(*sel_range[0])]
    sel_range1 = sel_range[1]
    if sel_range1 != (0, 0):
        sel += ['...'] + all_sel[slice(*sel_range1)]
    return sel

def get_indices(indices):

    type0 = range
    if isinstance(indices, range):
        ind = indices
    elif isinstance(indices, slice):
        ind = range(indices.stop)[indices]
    else:
        if isinstance(indices, (tuple, list)):
            ind = indices
        elif isinstance(indices, (np.ndarray)):
            ind = indices.flatten().tolist()
        else:
            ind = [indices]

        type0 = type(ind[0])
        if type0 not in (int, str):
            raise ValueError(f'Invalid indices type: {type0}!')
        errors = [i for i in ind if not isinstance(i, type0)]
        if errors:
            raise error.GeomError('The data types are different for all items!') 
        
    return ind, type0

def get_info(ds, show_gcps = True, show_metadata = True, show_rat = False, show_colortable = False,
             show_nodata = True, show_mask = False, list_mdd = False, show_file_list = True, all_metadata = False, 
             ooptions = []):
    
    new_options = ['-json']
    if not show_gcps:
        new_options += ['-nogcp']
    if not show_metadata:
        new_options += ['-nomd']

    if not show_rat:
        new_options += ['-norat']
    if not show_colortable:
        new_options += ['-noct']
    if not show_nodata:
        new_options += ['-nonodata']
    if not show_mask:
        new_options += ['-nomask']
    if list_mdd:
        new_options += ['-listmdd']
    if not show_file_list:
        new_options += ['-nofl']
    if all_metadata:
        new_options += ['-mdd', 'all']
    new_options += ooptions

    me_str = _gdal.InfoInternal(ds, _gdal.new_GDALInfoOptions(new_options))

    if isinstance(me_str, str):
        import json
        json_dict = json.loads(me_str)
    else:
        json_dict = {}

    return json_dict

# ## 注册 GDAL 功能
# #### gdal
# _gdal.Dataset_swigregister(BaseDataSet)
# _gdal.Driver_swigregister(BaseDriver)
# _gdal.GDALInfoOptions_swigregister(BaseInfoOptions)
# _gdal.ColorTable_swigregister(BaseColorTable)
# _gdal.Band_swigregister(BaseBand)

# #### osr
# _osr.SpatialReference_swigregister(BaseSpatialReference)
# _osr.AreaOfUse_swigregister(BaseAreaOfUse)
# _osr.CoordinateTransformation_swigregister(BaseCoordinateTransformation)

# #### ogr
# _ogr.Layer_swigregister(BaseLayer)
# _ogr.Feature_swigregister(BaseFeature)
# _ogr.Geometry_swigregister(Geometry)
# _ogr.FeatureDefn_swigregister(BaseFeatureDefn)
# _ogr.FieldDefn_swigregister(BaseFieldDefn)

# _gdal.GDALWarpAppOptions_swigregister(GDALWarpAppOptions)
# _gdal.GDALTranslateOptions_swigregister(GDALTranslateOptions)
# _gdal.GDALVectorTranslateOptions_swigregister(GDALVectorTranslateOptions)
# _gdal.GDALBuildVRTOptions_swigregister(GDALBuildVRTOptions)
# _gdal.GDALDEMProcessingOptions_swigregister(GDALDEMProcessingOptions)
###########################################################################
_gdal.PushErrorHandler('CPLQuietErrorHandler')
_gdal.SetConfigOption('TIFF_USE_OVR', 'YES')
_gdal.SetConfigOption('GTIFF_VIRTUAL_MEM_IO', 'IF_ENOUGH_RAM')
_gdal.SetConfigOption('GDAL_NUM_THREADS', 'ALL_CPUS')
_gdal.SetConfigOption('GTIFF_DIRECT_IO', 'YES')
_gdal.SetConfigOption('OGR_GPKG_NUM_THREADS', '4')

_gdal.SetConfigOption('CPL_DEBUG', 'OFF')
_gdal.SetConfigOption('CPL_LOG_ERRORS', 'OFF')

_gdal.SetConfigOption('OGR_ENABLE_PARTIAL_REPROJECTION', 'TRUE')
_gdal.SetConfigOption('OGR_SQLITE_SYNCHRONOUS', 'OFF')
_gdal.SetConfigOption('SQLITE_USE_OGR_VFS', 'YES')
_gdal.SetConfigOption('GDAL_CONTINUE_ON_ERROR', 'YES')  # 尝试让GDAL在遇到错误时继续执行
_gdal.SetConfigOption('GDAL_VRT_ENABLE_PYTHON', 'YES')
_gdal.SetConfigOption('GDAL_ARRAY_OPEN_BY_FILENAME', 'TRUE')
_gdal.SetConfigOption('OGR_ORGANIZE_POLYGONS', 'SKIP')






