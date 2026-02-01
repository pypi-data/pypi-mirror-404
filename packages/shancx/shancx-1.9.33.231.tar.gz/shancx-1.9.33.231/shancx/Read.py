
import xarray as xr
import numpy as np
import gzip
import tempfile
import os
backend_kwargs = {
    'errors': 'ignore',  
    # 'errors': 'raise'   
    # 'errors': 'warn'    
}
def getGrib(filepath):
    tmp_path = filepath 
    if filepath.endswith('.gz'):
        with gzip.open(filepath, 'rb') as f:
            with tempfile.NamedTemporaryFile(suffix='.grib2', delete=False) as tmp:
                tmp.write(f.read())
                tmp_path = tmp.name   
    try:
        ds = xr.open_dataset(tmp_path, engine='cfgrib', backend_kwargs=backend_kwargs)
        var_name = list(ds.data_vars)[0]
        data_var = ds[var_name] 
        data_values = np.where(data_var.values < -900, np.nan, data_var.values)
        if 'latitude' in ds.coords and 'longitude' in ds.coords:
            lats = ds.latitude.values
            lons = ds.longitude.values
        elif 'lat' in ds.coords and 'lon' in ds.coords:
            lats = ds.lat.values
            lons = ds.lon.values
        elif hasattr(ds, 'latitude') and hasattr(ds, 'longitude'):
            lats = ds.latitude.values
            lons = ds.longitude.values
        else:
            for var_name in ds.data_vars:
                var = ds[var_name]
                if hasattr(var, 'latitude') and hasattr(var, 'longitude'):
                    lats = var.latitude.values
                    lons = var.longitude.values
                    break
            else:
                raise ValueError("未找到经纬度坐标")       
        return {
            'data': data_values,
            'lats': lats,
            'lons': lons 
        }        
    finally:
        os.unlink(tmp_path)

"""
input_Path = './Composite_00.50_20250701-010044.grib2.gz'
result = getGrib(input_Path)
"""

import pygrib
import numpy as np
import pandas as pd
def readGrib(file_path, target_param=None):
    try:
        with pygrib.open(file_path) as grbs:
            field_info = []
            for grb in grbs:
                field_info.append({
                                   'messageNumber': grb.messagenumber,
                                   'parameterName': getattr(grb, 'parameterName', 'N/A'),
                                   'shortName': getattr(grb, 'shortName', 'N/A'),
                                   'level': getattr(grb, 'level', -999),
                                   'typeOfLevel': getattr(grb, 'typeOfLevel', 'N/A'),
                                   'validDate': getattr(grb, 'validDate', 'N/A'),
                                   'units': getattr(grb, 'units', 'N/A'),
                                   'shape': grb.values.shape
                                 })             
            if target_param:
                try:
                    grb = grbs.select(shortName=target_param)[0]
                except:
                    try:
                        grb = grbs.select(parameterName=target_param)[0]
                    except:
                        raise ValueError(f"未找到参数: {target_param}")
            else:
                grb = grbs[1]
            data = grb.values
            lats, lons = grb.latlons()            
            return {
                'data': data,
                'lats': lats,
                'lons': lons,
                'metadata': {
                    'parameterName': grb.parameterName,
                    'level': grb.level,
                    'validDate': grb.validDate,
                    'units': grb.units
                }
            }            
    except Exception as e:
        print(f"GRIB读取错误: {str(e)}")
        return None
"""
if __name__ == "__main__":
    path = "/mnt/wtx_weather_forecast/CMA_DATA/NAFP/EC/C1D/2024/2024112720/ECMFC1D_PRTY_1_2024112712_GLB_1_2.grib2"
    result = readGrib(path)    
    if result:
        print("\n数据矩阵形状:", result['data'].shape)
        print("经度范围:", np.min(result['lons']), "~", np.max(result['lons']))
        print("纬度范围:", np.min(result['lats']), "~", np.max(result['lats']))
        print("参数单位:", result['metadata']['units'])
"""
  

