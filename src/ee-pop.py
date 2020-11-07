# -*- coding: utf-8 -*-
"""
Created on Sat Nov  7 09:25:48 2020

@author: elmsc

This script uses google earth engine to aggregate population by subarea using the 
WorldPop project estimates. 

"""
#%% Import earth engine api

import ee
print(ee.__version__)

#ee.Authenticate()
ee.Initialize()

#%% import and filter world pop estimates to area of interest

# location of GEE feature
aoi = ee.FeatureCollection('users/camargop/sen_adm4_raster_agg')

ee_aoi = ee.ImageCollection("WorldPop/GP/100m/pop")
ee_aoi = ee_aoi.filterBounds(aoi)
ee_aoi = ee_aoi.filterDate('2020-01-01', '2020-09-29')

#%% will return image metedata and band information

#ee_aoi.getInfo()
#ee_aoi.first().bandNames().getInfo()

#%% take the median of estimates between image collections and compute zonal stats

median = ee.Image(ee_aoi.median())


# zonal stats scale must be the same as spatial resolution of image
# Admi4 or NOMCR can be used to calc but both have dups, consider making a new id 
sums = median.reduceRegions(**{
  'collection': aoi.select(['Admi4']),
  'reducer': ee.Reducer.sum(),
  'scale': 100,
})

# sends request to gee and returns output
pop_sums = sums.getInfo()

#%% transform ee output to dataframe 

import pandas as pd

list_df = []

for i in pop_sums['features']:
    print(i['properties'])
    list_df.append(i['properties'])

df = pd.DataFrame(list_df)

# only use if NOMCR is used to aggregate zones
#df['NOMCR'] = df['NOMCR'].map(lambda x: 'unknown' if x == '' else x)


#%% left join data zonal stats to sub area boundaries

import geopandas as gpd
import fiona

gdb_loc = 'G:/.shortcut-targets-by-id/1ihZCdFkFKljvEUetC8IiiE7JEDSGKA4J/hersh_lab/sahel/senegal/Senegal_geodatabase/SEN.gdb'
layer_list = fiona.listlayers(gdb_loc)
country = gpd.read_file(gdb_loc, driver='FileGDB', layer='sen_admbnda_adm4_comrurales_gov')

#country['NOMCR'] = country['NOMCR'].map(lambda x: 'unknown' if x == ' ' else x)

country = pd.merge(country, df, on="Admi4", how='left')

#%% easy population visualization

import matplotlib.pyplot as plt

# makes the map a bit easier to read
country['per_1000'] = country['sum'] /1000

fig, ax = plt.subplots(1, 1)

ax = country.plot(column='per_1000', ax=ax, legend=True,markersize=5,
                   legend_kwds={'orientation': "horizontal"})

ax.set_axis_off()
ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)

#width, height
ax.text(-14,9, "Population per 1000 people", fontsize=15, verticalalignment='center', horizontalalignment='center')
ax.set_title('Senegal Population', fontsize= 20)

#%% It is common to segment population data to make a cleaner choropleth map

# from pysal package
import mapclassify as mc

# Natural breaks algorithm often used in GIS mapping (Jenks is good too)
classifier = mc.NaturalBreaks.make(k=4)
country['natural_breaks'] = country[['per_1000']].apply(classifier)

#%% Attach min and max for each natural break for interprebility 

import collections
grouped = country.groupby('natural_breaks')

import matplotlib.patches as mpatches

legend_dict = collections.OrderedDict([])

for cl, valds in grouped:
   minv = valds['per_1000'].min()
   maxv = valds['per_1000'].max()
   legend_dict.update({"Class {}: {} - {}".format(cl, minv, maxv): "white"})
   print("Class {}: {} - {}".format(cl, minv, maxv))
   
fig, ax = plt.subplots()
country.plot(ax=ax, column="natural_breaks", linewidth=0, legend=True)
ax.set_axis_off()

ax.set_title('Senegal Population', fontsize= 15)

patchList = []

for key in legend_dict:
   data_key = mpatches.Patch(color=legend_dict[key], label=key)
   patchList.append(data_key)

plt.legend(handles=patchList, loc='lower center', bbox_to_anchor=(0.5, -0.6), ncol=1)

ax.text(-14,9, "Population per 1000 people", fontsize=15, verticalalignment='center', horizontalalignment='center')

plt.savefig('../output/images/senegal.png', bbox_inches="tight", pad_inches=0)