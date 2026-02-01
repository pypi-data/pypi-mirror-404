
    
import ssl
import urllib.request
ssl._create_default_https_context = ssl._create_unverified_context
import datetime
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from hjnwtx.colormap import cmp_hjnwtx
import os
def plotGlobal(b, latArr1, lonArr1, cmap='summer', title='Global QPF Data Visualization',saveDir = "./plotGlobal",ty=None,name="plotGlobal" ):
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S") 
    plt.figure(figsize=(20, 10), dpi=100)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, facecolor='none')  # 陆地无色
    ax.add_feature(cfeature.OCEAN, facecolor='none')  # 海洋无色
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')  # 海岸线黑色
    ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, edgecolor='black')  # 国界线黑色
    ax.add_feature(cfeature.LAKES, alpha=0.3, facecolor='none', edgecolor='gray')  # 湖泊无色，灰色边界
    ax.add_feature(cfeature.RIVERS, edgecolor='gray', linewidth=0.5)  # 河流灰色
    lon_grid, lat_grid = np.meshgrid(lonArr1, latArr1)
    stride = 10  # 每10个点取1个
    cmap = {
        "radar": cmp_hjnwtx["radar_nmc"],
        "pre": cmp_hjnwtx["pre_tqw"],
        None: 'summer'
    }.get(ty)

    minmax = {
        "radar": [0,80],
        "pre": [0,20],
        None: [np.nanmin(b),np.nanmax(b)]
    }.get(ty)

    setlabel = {
        "radar": 'Composite Reflectivity (Radar)\nUnit: (dBZ)',
        "pre": 'Precipitation\nUnit: (mm)',
        None: 'Data'
    }.get(ty)

    img = ax.pcolormesh(lon_grid[::stride, ::stride], 
                       lat_grid[::stride, ::stride],
                       b[::stride, ::stride],
                       cmap=cmap,  
                       shading='auto',
                       vmin=minmax[0],
                       vmax=minmax[1],
                       transform=ccrs.PlateCarree())
    cbar = plt.colorbar(img, ax=ax, orientation='vertical', pad=0.05, shrink=0.6)
    cbar.set_label(setlabel, fontsize=12)
    ax.set_xticks(np.arange(-180, 181, 30), crs=ccrs.PlateCarree())
    ax.set_yticks(np.arange(-90, 91, 15), crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=True))
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.gridlines(color='gray', linestyle=':', alpha=0.5)
    ax.set_title(title, fontsize=16, pad=20)
    ax.set_global()     
    plt.tight_layout()
    os.makedirs(saveDir, exist_ok=True)
    plt.savefig(f"./{saveDir}/plotGlobal_glob{now_str}_{name}.png", dpi=300, bbox_inches="tight")  
    plt.close()
    
"""
plotGlobal(b, latArr1, lonArr1, 
                title='Global Meteorological Data',ty="radar")
"""

import ssl
import urllib.request
ssl._create_default_https_context = ssl._create_unverified_context
import datetime
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from hjnwtx.colormap import cmp_hjnwtx
import os
def plotGlobalTtf(b, latArr1, lonArr1, cmap='summer', title='Global QPF Data Visualization', saveDir="./plotGlobal", ty=None, name=1,font_path=None):
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S") 
    import matplotlib.pyplot as plt
    import matplotlib
    import matplotlib.font_manager as fm
    font_path = "/mnt/wtx_weather_forecast/scx/sever7/微软雅黑.ttf" if font_path is None else font_path
    font_kwargs = {}    
    if os.path.exists(font_path):
        try:
            fm.fontManager.addfont(font_path)
            font_prop = fm.FontProperties(fname=font_path)
            font_name = font_prop.get_name()
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.sans-serif'] = [font_name]
            plt.rcParams['axes.unicode_minus'] = False
            font_kwargs = {'fontproperties': font_prop}
            print(f"成功加载字体: {font_name}")            
        except Exception as e:
            print(f"加载指定字体失败: {e}")
            # 尝试使用系统字体
            try:
                plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
            except:
                pass
    else:
        print(f"警告: 字体文件不存在: {font_path}")
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass    
    plt.figure(figsize=(20, 10), dpi=100)
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, facecolor='none')  # 陆地无色
    ax.add_feature(cfeature.OCEAN, facecolor='none')  # 海洋无色
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')  # 海岸线黑色
    ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, edgecolor='black')  # 国界线黑色
    ax.add_feature(cfeature.LAKES, alpha=0.3, facecolor='none', edgecolor='gray')  # 湖泊无色，灰色边界
    ax.add_feature(cfeature.RIVERS, edgecolor='gray', linewidth=0.5)  # 河流灰色
    lon_grid, lat_grid = np.meshgrid(lonArr1, latArr1)
    stride = 10  # 每10个点取1个
    cmap = {
        "radar": cmp_hjnwtx["radar_nmc"],
        "pre": cmp_hjnwtx["pre_tqw"],
        None: 'summer'
    }.get(ty)
    minmax = {
        "radar": [0,80],
        "pre": [0,20],
        None: [np.nanmin(b),np.nanmax(b)]
    }.get(ty)

    setlabel = {
        "radar": '雷达组合反射率\n单位：（dbz）',
        "pre": '降雨量\n单位：（mm）',
        None: '数据'
    }.get(ty)
    img = ax.pcolormesh(lon_grid[::stride, ::stride], 
                       lat_grid[::stride, ::stride],
                       b[::stride, ::stride],
                       cmap=cmap,  
                       shading='auto',
                       transform=ccrs.PlateCarree(), vmin=minmax[0], vmax=minmax[1])
    cbar = plt.colorbar(img, ax=ax, orientation='vertical', pad=0.05, shrink=0.6)
    if font_kwargs:
        cbar.set_label(setlabel, fontsize=12, **font_kwargs)
    ax.set_xticks(np.arange(-180, 181, 30), crs=ccrs.PlateCarree())
    ax.set_yticks(np.arange(-90, 91, 15), crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=True))
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.gridlines(color='gray', linestyle=':', alpha=0.5)
    ax.set_title(title, fontsize=16, pad=20)    
    ax.set_global()     
    plt.tight_layout()
    os.makedirs(saveDir, exist_ok=True)
    plt.savefig(f"./{saveDir}/plotScatter_glob{now_str}_{ty}_{name}.png", dpi=300, bbox_inches="tight")  
    plt.close()
    
'''
plotGlobal(satH9[0], latArrsatH9, lonArrsatH9, title=f'全球气象雷达组合反射率分布图',saveDir="./plotGlobal", ty="radar",name = "")
'''

import datetime
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from hjnwtx.colormap import cmp_hjnwtx
import os

def plotGlobalPlus(b, latArr1, lonArr1, cmap='summer', title='Global QPF Data Visualization', 
               saveDir="./plotGlobal", ty=None, cartopy_data_dir="./share/cartopy"):
    os.environ['CARTOPY_USER_BACKGROUNDS'] = cartopy_data_dir
    os.makedirs(cartopy_data_dir, exist_ok=True)
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S") 
    plt.figure(figsize=(20, 10), dpi=100)
    ax = plt.axes(projection=ccrs.PlateCarree())
    try:
        ax.add_feature(cfeature.LAND.with_scale('110m'), facecolor='none')
        ax.add_feature(cfeature.OCEAN.with_scale('110m'), facecolor='none')
        ax.add_feature(cfeature.COASTLINE.with_scale('110m'), linewidth=0.8, edgecolor='black')
        ax.add_feature(cfeature.BORDERS.with_scale('110m'), linestyle='-', linewidth=0.5, edgecolor='black')
        ax.add_feature(cfeature.LAKES.with_scale('110m'), alpha=0.3, facecolor='none', edgecolor='gray')
        ax.add_feature(cfeature.RIVERS.with_scale('110m'), edgecolor='gray', linewidth=0.5)
    except:
        ax.add_feature(cfeature.LAND, facecolor='none')
        ax.add_feature(cfeature.OCEAN, facecolor='none')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')
        ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, edgecolor='black')
        ax.add_feature(cfeature.LAKES, alpha=0.3, facecolor='none', edgecolor='gray')
        ax.add_feature(cfeature.RIVERS, edgecolor='gray', linewidth=0.5)
    lon_grid, lat_grid = np.meshgrid(lonArr1, latArr1)
    stride = 10  # 每10个点取1个
    cmap = {
        "radar": cmp_hjnwtx["radar_nmc"],
        "pre": cmp_hjnwtx["pre_tqw"],
        None: 'summer'
    }.get(ty)

    minmax = {
        "radar": [0,80],
        "pre": [0,20],
        None: [np.nanmin(b),np.nanmax(b)]
    }.get(ty)

    setlabel = {
        "radar": 'Composite Reflectivity (Radar)\nUnit: (dBZ)',
        "pre": 'Precipitation\nUnit: (mm)',
        None: 'Data'
    }.get(ty)

    img = ax.pcolormesh(lon_grid[::stride, ::stride], 
                       lat_grid[::stride, ::stride],
                       b[::stride, ::stride],
                       cmap=cmap,  
                       shading='auto',
                       vmin = minmax[0],
                       vmax = minmax[1],
                       transform=ccrs.PlateCarree())
    cbar = plt.colorbar(img, ax=ax, orientation='vertical', pad=0.05, shrink=0.6)
    cbar.set_label(setlabel , fontsize=12)
    ax.set_xticks(np.arange(-180, 181, 30), crs=ccrs.PlateCarree())
    ax.set_yticks(np.arange(-90, 91, 15), crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=True))
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.gridlines(color='gray', linestyle=':', alpha=0.5)
    ax.set_title(title, fontsize=16, pad=20)
    ax.set_global()
    plt.tight_layout()
    os.makedirs(saveDir, exist_ok=True)
    save_path = os.path.join(saveDir, f"plotScatter_glob{now_str}.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close()    
    print(f"图像已保存到: {save_path}")
    return save_path
    
"""
if __name__ == "__main__":
    plotGlobal(
               b=CR,
               latArr1=latArr,
               lonArr1=lonArr,
               title='Global Precipitation Forecast',
               saveDir='./output',
               ty='pre',   
               cartopy_data_dir='./share/cartopy'
              )
"""


import ssl
import urllib.request
ssl._create_default_https_context = ssl._create_unverified_context
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
import datetime
import numpy as np
def plotScatter(df1, title = "Total number ",saveDir="plotScatter", map_background=True, 
                projection=ccrs.PlateCarree(), figsize=(12, 8)):
    now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")    
    if map_background:
        fig = plt.figure(figsize=figsize)
        ax = plt.axes(projection=projection)
        ax.add_feature(cfeature.LAND, facecolor='none', alpha=0.3)
        ax.add_feature(cfeature.OCEAN, facecolor='none', alpha=0.3)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')
        ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, edgecolor='black')
        ax.add_feature(cfeature.LAKES, alpha=0.3, facecolor='gray')
        ax.add_feature(cfeature.RIVERS, edgecolor='gray', linewidth=0.5)
        ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        if len(df1) > 0:
            buffer = 5  # 边距
            min_lon, max_lon = df1["Lon"].min() - buffer, df1["Lon"].max() + buffer
            min_lat, max_lat = df1["Lat"].min() - buffer, df1["Lat"].max() + buffer
            # ax.set_extent([min_lon, max_lon, min_lat, max_lat], crs=ccrs.PlateCarree())
            ax.set_global() 
        else:
            ax.set_global()  # 如果没有数据，显示全球
        scatter = ax.scatter(
            df1["Lon"],  
            df1["Lat"],  
            s=0.5,        
            alpha=0.7,   
            edgecolor="red",   
            linewidth=0.5,
            color='red',
            transform=ccrs.PlateCarree(),  # 重要：指定坐标变换
            zorder=10  # 确保散点在地图上方
        )        
        plt.title(title, fontsize=14, pad=20)        
    
    plt.tight_layout()  
    os.makedirs(saveDir, exist_ok=True)
    plt.savefig(f"./{saveDir}/plotScatter_{now_str}.png", dpi=300, bbox_inches="tight")  
    plt.close()    
    print(f"散点图已保存到: ./{saveDir}/plotScatter_{now_str}.png")
    print(f"总共绘制了 {len(df1)} 个点")

"""
plotScatter(df2,title = f" Total number of stations ", saveDir="scatter_maps")
"""

import ssl
import urllib.request
ssl._create_default_https_context = ssl._create_unverified_context
import datetime
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from hjnwtx.colormap import cmp_hjnwtx
from shancx import crDir
def plotBorder(UTCstr, nclon, nclat, cr, fig_title,savepath="./plotBorder", datatype=None,font_path=None,shp_file="./"):
    myfont = mpl.font_manager.FontProperties(fname = font_path, size = 12) 
    figpath = f"{savepath}/fig/{UTCstr[:4]}/{UTCstr[:8]}/{fig_title}.PNG"
    crDir(figpath)
    lonmin = np.min(nclon)
    lonmax = np.max(nclon)
    latmin = np.min(nclat)
    latmax = np.max(nclat)    
    # 创建图形和坐标轴
    fig = plt.figure(figsize=(6, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())    
    # 1. 首先添加Cartopy的基础地理要素（作为底层）
    ax.add_feature(cfeature.OCEAN, facecolor='none')      # 海洋无色
    ax.add_feature(cfeature.LAND, facecolor='none')       # 陆地无色
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='gray')      # 海岸线
    ax.add_feature(cfeature.BORDERS, linestyle='-', linewidth=0.5, edgecolor='gray')  # 国界线
    ax.add_feature(cfeature.LAKES, alpha=0.3, facecolor='none', edgecolor='gray')      # 湖泊
    ax.add_feature(cfeature.RIVERS, edgecolor='gray', linewidth=0.5)                   # 河流
    ax.set_xticks(np.arange(lonmin, lonmax + 0.1, 15))
    ax.set_yticks(np.arange(latmin, latmax + 0.1, 10))
    ax.set_xlim([nclon[0], nclon[-1]])
    ax.set_ylim([nclat[-1], nclat[0]])
    ax.xaxis.set_major_formatter(LongitudeFormatter())                       
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.tick_params(axis='both', labelsize=10)    
    # 3. 叠加自定义的省界矢量（显示在基础地理要素之上）
    if os.path.exists(shp_file) and shp_file[-4:]==".shp" :
        try:
            shp = gpd.read_file(shp_file).boundary
            # 使用较细的线宽，避免与国界线混淆
            shp.plot(ax=ax, edgecolor='grey', linewidth=0.5, linestyle='-')
        except Exception as e:
            print(f"警告：读取矢量文件 {shp_file} 失败: {e}")
    else:
        print(f"警告：矢量文件 {shp_file} 不存在，将只绘制Cartopy地理要素。")
    ax.set_title(fig_title, fontsize=12, loc='center', fontproperties=myfont)     
    # 5. 绘制雷达或降雨数据（在最上层）
    if datatype == 'radar':
        clevels = [0, 10, 20, 30, 40, 50, 60, 70]
        colors = ['#62e6eaff', '#00d72eff', '#fefe3fff', '#ff9a29ff', '#d70e15ff', '#ff1cecff', '#af91edff']
    elif datatype == 'rain':  
        clevels = [0.1, 2.5, 8, 16, 200]
        colors = ["#a6f28f", "#3dba3d", "#61b8ff", "#0000ff"]
    cs = plt.contourf(nclon, nclat, cr, levels=clevels, colors=colors, extend='both')
    cb = plt.colorbar(cs, fraction=0.022, pad=0.03)
    cb.set_ticks(clevels[:-1])
    cb.set_ticklabels([str(level) for level in clevels[:-1]], fontproperties=myfont)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(myfont)
    plt.savefig(figpath, dpi=300, bbox_inches='tight') 
    print(f"{fig_title.split('_')[0]}绘制完成: {figpath}")
    plt.close()

"""
latArr = np.linspace(27, -13, 2000 )
lonArr = np.linspace(70, 150, 4000) 
font_path = '/mnt/wtx_weather_forecast/scx/sever7/微软雅黑.ttf'

fig_title = f"实况雷达回波_{UTCstr}_test"          
baseCR[:,900:3700] = CR
plotBorder(UTCstr,lonArr,latArr,baseCR,fig_title,datatype="radar",font_path=font_path) 
fig_title = f"卫星反演雷达回波_{UTCstr}"
"""

import matplotlib as mpl 
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import geopandas as gpd
from cartopy.mpl.ticker import LongitudeFormatter,LatitudeFormatter
import numpy as np
from shancx import crDir
def plot_fig1(cr,nclat,nclon,fig_title,datatype=None,savepath=None,font_path=None,shp_file=None):
    figpath = f"{savepath}/fig/{fig_title.split('_')[1][:4]}/{fig_title.split('_')[1][:8]}/{fig_title.split('_')[1][:12]}/{fig_title}.PNG"
    # if not os.path.exists(figpath):
    lonmin = np.min(nclon)
    lonmax = np.max(nclon)
    latmin = np.min(nclat)
    latmax = np.max(nclat)
    myfont = mpl.font_manager.FontProperties(fname = font_path, size = 12) 
    fig = plt.figure(figsize=(6,6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_xticks(np.arange(lonmin, lonmax + 0.1, 15))
    ax.set_yticks(np.arange(latmin, latmax + 0.1, 10))
    ax.set_xlim([lonmin, lonmax])
    ax.set_ylim([latmin, latmax])
    ax.xaxis.set_major_formatter(LongitudeFormatter()) #刻度格式转换为经纬度样式                       
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.tick_params(axis = 'both',labelsize = 10)
    shp = gpd.read_file(shp_file).boundary
    shp.plot(ax=ax, edgecolor='grey', linewidth=0.7)
    ax.set_title(fig_title, fontsize = 12, loc='center',fontproperties = myfont) 
    if datatype == 'radar':
        clevels = [0,10, 20, 30, 40, 50, 60, 70]
        colors = ['#62e6eaff','#00d72eff','#fefe3fff','#ff9a29ff','#d70e15ff','#ff1cecff','#af91edff']
        # colors = ["#449ded", "#62e6ea", "#68f952", "#0000ff"]
    elif datatype == 'rain':  
        clevels = [0.1, 2.5, 8, 16,200]
        colors = ["#a6f28f", "#3dba3d", "#61b8ff", "#0000ff"]
    if datatype == 'sat':
        clevels = [150,170, 190, 210, 230, 250, 270, 290,310]
        colors = [
                '#00008B',  # 150K 深蓝
                '#0066CC',  # 170K 钴蓝
                '#00BFFF',  # 190K 深天蓝
                '#40E0D0',  # 210K 绿松石
                '#00FF00',  # 230K 亮绿
                '#FFFF00',  # 250K 黄色
                '#FFA500',  # 270K 橙色
                '#FF4500',  # 290K 橙红
                '#FF0000'   # 310K 红色
            ]
    cs = plt.contourf(nclon, nclat, cr, levels=clevels, colors=colors)    
    cb = plt.colorbar(cs, fraction=0.022)
    cb.set_ticks(clevels[:-1])
    cb.set_ticklabels([str(level) for level in clevels[:-1]],fontproperties = myfont)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(myfont)
    crDir(figpath)
    plt.savefig(figpath, dpi=300, bbox_inches='tight') 
    print(f"{fig_title.split('_')[0]}绘制完成: {figpath}")
    plt.close()
"""
font_path = './shp/微软雅黑.ttf'
myfont = mpl.font_manager.FontProperties(fname = font_path, size = 12) 
UTCstr="202508280000"
shp_file = "./shp/province_9south.shp"
savepath = f"./FY4BBIG"
fig_title = f"卫星反演雷达回波_{UTCstr}"
# base[20:1070,75:1625] = satCR
plot_fig(data,result['lats'],result['lons'],fig_title,datatype="radar")
"""
 
