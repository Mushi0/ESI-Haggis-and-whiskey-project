import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
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

    # gdf = gpd.GeoDataFrame(data['District ID'], geometry = geometry)
    # gdf = gpd.GeoDataFrame(data['total_demand'], geometry = geometry)
    gdf = gpd.GeoDataFrame(data['capacity_not_used'], geometry = geometry)

    gdf = gdf.set_crs(epsg = 4326, inplace=True)
    gdf = gdf.to_crs(epsg = 3857)

    plt.figure()
    ax = gdf.plot(figsize = (16, 8))
    # ax = gdf.plot(column = 'total_demand', figsize = (16, 8), cmap = 'winter', legend = True)
    # ax = gdf.plot(column = 'capacity_used', figsize = (16, 8), cmap = 'winter', legend = True)
    ctx.add_basemap(ax)
    # crs = {'init': 'epsg:4326'}
    # ctx.add_basemap(ax, crs = crs)
    plt.savefig(save_name)

def plot_map_chosen(data, data_chosen, save_name = 'map_chosen.png'):
    geometry = [Point(xy) for xy in zip(data['lat'], data['lon'])]
    geometry_chosen = [Point(xy) for xy in zip(data_chosen['lat'], data_chosen['lon'])]

    # gdf = gpd.GeoDataFrame(data['District ID'], geometry = geometry)
    # gdf = gpd.GeoDataFrame(data['total_demand'], geometry = geometry)
    gdf = gpd.GeoDataFrame(data['capacity_not_used'], geometry = geometry)
    # gdf_chosen = gpd.GeoDataFrame(data_chosen['District ID'], geometry = geometry_chosen)
    # gdf_chosen = gpd.GeoDataFrame(data_chosen['total_demand'], geometry = geometry_chosen)
    gdf_chosen = gpd.GeoDataFrame(data_chosen['capacity_not_used'], geometry = geometry_chosen)

    gdf = gdf.set_crs(epsg = 4326, inplace=True)
    gdf = gdf.to_crs(epsg = 3857)
    gdf_chosen = gdf_chosen.set_crs(epsg = 4326, inplace=True)
    gdf_chosen = gdf_chosen.to_crs(epsg = 3857)

    plt.figure()
    ax = gdf.plot(figsize = (16, 8))
    # ax = gdf.plot(column = 'total_demand', figsize = (16, 8), cmap = 'winter', legend = True)
    # gdf_chosen.plot(ax = ax, color = 'orange')
    # gdf_chosen.plot(ax = ax, column = 'total_demand', cmap = 'autumn', legend = True)
    gdf_chosen.plot(ax = ax, column = 'capacity_not_used', cmap = 'autumn', legend = True)
    ctx.add_basemap(ax)
    plt.savefig(save_name)

def plot_map_lines(data, data_chosen, chosen, assign, save_name = 'plot_map_lines.png'):
    geometry = [Point(xy) for xy in zip(data['lat'], data['lon'])]
    geometry_chosen = [Point(xy) for xy in zip(data_chosen['lat'], data_chosen['lon'])]

    gdf = gpd.GeoDataFrame(data['District ID'], geometry = geometry)
    gdf_chosen = gpd.GeoDataFrame(data_chosen['District ID'], geometry = geometry_chosen)

    gdf = gdf.set_crs(epsg = 4326, inplace=True)
    gdf = gdf.to_crs(epsg = 3857)
    gdf_chosen = gdf_chosen.set_crs(epsg = 4326, inplace=True)
    gdf_chosen = gdf_chosen.to_crs(epsg = 3857)

    line = [np.NaN]*len(data)
    for i, fac in enumerate(chosen):
        for j in assign[i]:
            line[j] = LineString([[gdf_chosen.geometry.x[fac], gdf_chosen.geometry.y[fac]], [gdf.geometry.x[j], gdf.geometry.y[j]]])
    gdf['LINE'] = line
    gdf_lines = gpd.GeoDataFrame(gdf, geometry='LINE')

    plt.figure()
    ax = gdf.plot(figsize = (16, 8))
    gdf_chosen.plot(ax = ax, color = 'orange')
    gdf_lines.plot(ax = ax, color = 'black')
    ctx.add_basemap(ax)
    plt.savefig(save_name)

# with open('log.txt') as f:
#     log_data = f.read()
# chosen = re.findall(r'Facility (.*?) open to serve customers: ', log_data)
# chosen = [int(i) for i in chosen]
with open('logs\log_2.txt') as f:
    log_data = f.read()
chosen_assign = re.findall(r'Facility (.*?) open to serve customers: (.*?)\n', log_data)
chosen = [int(item[0]) for item in chosen_assign]
assign = [[int(i) for i in item[1].split(', ')] for item in chosen_assign]

# data = read_convert('Data\Potential Locations.xlsx', easting = 'X (Easting)', northing = 'Y (Northing)', lat = 'lat', lon = 'lon')
data = read_convert('Data\Postcode Districts.xlsx', easting = 'X (Easting)', northing = 'Y (Northing)', lat = 'lat', lon = 'lon')
data_capacity = pd.read_excel('Data\Potential Locations.xlsx')['Annual capacity']
data['total_demand'] = data[['Group 1', 'Group 2', 'Group 3', 'Group 4']].sum(axis = 1)
for i, fac in enumerate(chosen):
    data.loc[fac, 'capacity_not_used'] = (sum([data['total_demand'][j] for j in assign[i]]))/data_capacity[fac]*100
data_chosen = data.iloc[chosen]

# plot_map(data)
plot_map_chosen(data, data_chosen)
plot_map_lines(data, data_chosen, chosen, assign)
