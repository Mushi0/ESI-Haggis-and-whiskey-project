import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point
import geopandas as gpd
import contextily as ctx
from pyproj import Proj, transform
import re

# used to convert the UK easting northing to lat/long
inProj = Proj(init = 'epsg:27700') #British National Grid
outProj = Proj(init = 'epsg:4326') #WGS84

def read_convert(file_name, easting = 'X (Easting)', northing = 'Y (Northing)', lat = 'lat', lon = 'lon'):
    '''
    Read the data and convert the easting/northing coordinates to lat/lon

    Input: file_name (str): name of the excel file to read from
            easting, northing (str): names of the columns containing the coordinates
            lat, lon (str): names of the lat/lon columns to add to the data set
    '''
    data = pd.read_excel(file_name) # read the data
    # convert to long/lat
    lats, lons = [], []
    for i in range(len(data)):
        lat, lon = transform(inProj, outProj, data.loc[i, easting], data.loc[i, northing])
        lats.append(lat)
        lons.append(lon)
    data['lat'] = lats
    data['lon'] = lons
    return data

def plot_map(data, save_name = 'map.png'):
    geometry = [Point(xy) for xy in zip(data['lat'], data['lon'])]

    gdf = gpd.GeoDataFrame(data['District ID'], geometry = geometry)

    gdf = gdf.set_crs(epsg = 4326, inplace=True)
    gdf = gdf.to_crs(epsg = 3857)

    plt.figure()
    ax = gdf.plot(figsize = (16, 8))
    ctx.add_basemap(ax)
    # crs = {'init': 'epsg:4326'}
    # ctx.add_basemap(ax, crs = crs)
    plt.savefig(save_name)

def plot_map_chosen(data, data_chosen, save_name = 'map_chosen.png'):
    geometry = [Point(xy) for xy in zip(data['lat'], data['lon'])]
    geometry_chosen = [Point(xy) for xy in zip(data_chosen['lat'], data_chosen['lon'])]

    gdf = gpd.GeoDataFrame(data['District ID'], geometry = geometry)
    gdf_chosen = gpd.GeoDataFrame(data_chosen['District ID'], geometry = geometry_chosen)

    gdf = gdf.set_crs(epsg = 4326, inplace=True)
    gdf = gdf.to_crs(epsg = 3857)
    gdf_chosen = gdf_chosen.set_crs(epsg = 4326, inplace=True)
    gdf_chosen = gdf_chosen.to_crs(epsg = 3857)

    plt.figure()
    ax = gdf.plot(figsize = (16, 8))
    gdf_chosen.plot(ax = ax, color = 'orange')
    ctx.add_basemap(ax)
    # crs = {'init': 'epsg:4326'}
    # ctx.add_basemap(ax, crs = crs)
    plt.savefig(save_name)

with open('log.txt') as f:
    log_data = f.read()
chosen = re.findall(r'Facility (.*?) open to serve customers: ', log_data)
chosen = [int(i) for i in chosen]

data = read_convert('Data\Potential Locations.xlsx', easting = 'X (Easting)', northing = 'Y (Northing)', lat = 'lat', lon = 'lon')
data_chosen = data.iloc[chosen]

plot_map(data)
plot_map_chosen(data, data_chosen)
