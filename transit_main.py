import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt

COUNTY_SHP = 'data/cb_2018_53_cousub_500k/cb_2018_53_cousub_500k.shp'
COUNTY_POP = 'data/cc-est2018-alldata-53.csv'

TRACT_SHP = 'data/tl_2010_53_tract00/tl_2010_53_tract00.shp'


def read_shapes(shapes_txt):
    df = pd.read_csv(shapes_txt)
    df['point'] = [Point(-long, lat) for long, lat in
                   zip(df['shape_pt_lon'], df['shape_pt_lat'])]
    shapes = df.groupby('shape_id')['point'].apply(
        lambda points: Polygon([[p.x, p.y] for p in points]))
    df = df.drop_duplicates('shape_id')
    df['geometry'] = shapes.values
    return gpd.GeoDataFrame(df[['shape_id', 'geometry']])


def load_bus_data():
    gtfs = 'data/gtfs/'
    dirs = os.listdir(gtfs)
    complete = None
    for dir in dirs:
        tokens = dir.split('_')
        syst = tokens[0]
        year = tokens[1]

        dir = gtfs + dir + "/"

        stop_times = pd.read_csv(dir + "stop_times.txt")
        stop_times = stop_times[['trip_id', 'arrival_time', 'departure_time', 'stop_id']]

        stops = pd.read_csv(dir + "stops.txt")
        stops['coordinate'] = [Point(long, lat) for long, lat in
                   zip(stops['stop_lon'], stops['stop_lat'])]
        stops = stops[['stop_id', 'stop_name', 'stop_desc', 'zone_id', 'coordinate']]
        stops = gpd.GeoDataFrame(stops, geometry='coordinate')

        merged_stops = stops.merge(right=stop_times, how='right', left_on='stop_id', right_on='stop_id')
        merged_stops['year'] = year
        merged_stops['system'] = syst

        if complete is None:
            complete = merged_stops
        else:
            complete.append(merged_stops)
    return complete


def load_county_pop():
    """
    Loads the county populations file and merges it with county shape data.
    """
    shapes = gpd.read_file(COUNTY_SHP)
    pop = pd.read_csv(COUNTY_POP)

    # turn year column into "real" years
    pop.loc[pop['YEAR'] < 3, 'YEAR'] = 3
    pop['YEAR'] += 2007

    # dissolve to counties
    shapes['COUNTYFP'] = shapes['COUNTYFP'].astype(int)
    shapes = shapes.dissolve(by='COUNTYFP')

    joined = pop.merge(right=shapes, how='left',
                       left_on='COUNTY', right_on='COUNTYFP')
    return joined


def load_tract_incomes():
    shapes = gpd.read_file(TRACT_SHP)
    inc_dirs = 'data/incomes/'
    dirs = os.listdir(inc_dirs)
    complete = None
    for dir in dirs:
        income = pd.read_csv(inc_dirs + dir)
        income['ID Geography'] = income['ID Geography'].apply(lambda tract: int(tract.split('US')[1]))
        if complete is None:
            complete = income
        else:
            complete.append(income)
    complete = complete.merge(right=shapes, how='left', left_on='ID Geography', right_on='CTIDFP00')
    return gpd.GeoDataFrame(complete)


def plot_income_change_over_availability(incomes, stops):
    # stops.plot()
    covered_tracts = gpd.sjoin(incomes, stops, how='inner', op='intersects')
    covered_2013 = covered_tracts[covered_tracts['Year'] == 2013]
    covered_2017 = covered_tracts[covered_tracts['Year'] == 2017]
    plt.savefig('income_change_over_availability.png')


def main():
    # county_pops = load_county_pop()
    # print(county_pops)
    stops = load_bus_data()
    incomes = load_tract_incomes()
    plot_income_change_over_availability(incomes, stops)


if __name__ == '__main__':
    main()
