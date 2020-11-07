# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 16:23:35 2020

@author: elmsc
"""

#%%
import geopandas as gpd
import pandas as pd
import rasterio
import fiona
import rasterstats 
import matplotlib.pyplot as plt

#%%

import os
os.chdir('G:/.shortcut-targets-by-id/1ihZCdFkFKljvEUetC8IiiE7JEDSGKA4J/hersh_lab/')

#%%

gdb_loc = 'sahel/senegal/Senegal_geodatabase/SEN.gdb'
layer_list = fiona.listlayers(gdb_loc)

#%%

country = gpd.read_file(gdb_loc, driver='FileGDB', layer='sen_admbnda_adm3_1m_gov_ocha_02032017')
country.plot()
country.describe()
country.info()

#%%

pop = rasterio.open('sahel/senegal/Senegal_geodatabase/output/tiff/sen_population_2020.tif')

# raster only viz
# fig, ax = plt.subplots(1,1,figsize=(15, 15))
# rasterio.plot.show(pop, title = 'population')

# raster and subarea viz
# fig, ax = plt.subplots(1,1,figsize=(15, 15))

# rasterio.plot.show(pop, ax=ax, title = 'population')
# country.plot(ax=ax, facecolor='None', edgecolor='yellow', linewidth=2)
# plt.show()

# del(ax,fig)

#%%

# raster vals to numpy array
print(pop.meta)
target_array = pop.read(1)
affine = pop.transform

#creates a list with zonal stats
sum_rf = rasterstats.zonal_stats(country, target_array, affine=affine,
                                 stats=['sum','mean'],
                                 geojson_out=True)

#%%

# turns list into dataframe
sum_pop = []
i = 0

while i < len(sum_rf):
    sum_pop.append(sum_rf[i]['properties'])
    i = i + 1

sum_rf_sub_area = pd.DataFrame(sum_pop)


#%%

country.reset_index(inplace=True)
sum_rf_sub_area.reset_index(inplace=True)

country = pd.merge(country, sum_rf_sub_area[['index', 'sum', 'mean']], on='index', how='inner')

country['per_1000'] = country['sum'] /1000
#%%

fig, ax = plt.subplots(1, 1)

ax = country.plot(column='per_1000', ax=ax, legend=True,markersize=5,
                   legend_kwds={'orientation': "horizontal"})

ax.set_axis_off()
ax.tick_params(left=False, labelleft=False, bottom=False, labelbottom=False)

#wh
ax.text(-14,9, "Population per 1000 people", fontsize=15, verticalalignment='center', horizontalalignment='center')
ax.set_title('Senegal Population', fontsize= 20)
#fig.set_size_inches(25,20)

#%%
import mapclassify as mc

classifier = mc.NaturalBreaks.make(k=5)
country['natural_breaks'] = country[['per_1000']].apply(classifier)

#%%
import collections
grouped = country.groupby('natural_breaks')

#%%

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