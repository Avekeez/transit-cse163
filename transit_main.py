import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point, Polygon

COUNTY_SHP = 'data/cb_2018_53_cousub_500k/cb_2018_53_cousub_500k.shp'
COUNTY_POP = 'data/cc-est2018-alldata-53.csv'

TRACT_SHP = 'data/tl_2010_53_tract00/tl_2010_53_tract00.shp'
TRACT_INC = 'data/Income by Location.csv'


def read_shapes(shapes_txt):
    df = pd.read_csv(shapes_txt)
    df['point'] = [Point(-long, lat) for long, lat in
                   zip(df['shape_pt_lon'], df['shape_pt_lat'])]
    shapes = df.groupby('shape_id')['point'].apply(
        lambda points: Polygon([[p.x, p.y] for p in points]))
    df = df.drop_duplicates('shape_id')
    # df = df.drop(['shape_pt_sequence', 'shape_pt_lat',
    #               'shape_pt_lon', 'point'], axis=1)
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

        # shapes = read_shapes(dir + "shapes.txt")
        # print(shapes)
        # shapes.to_csv("shapes_csv.")

        # trips = pd.read_csv(dir + "trips.txt")
        # print(trips)
        # trips.to_csv("trips.csv")

        stop_times = pd.read_csv(dir + "stop_times.txt")
        stop_times = stop_times[['trip_id', 'arrival_time', 'departure_time', 'stop_id']]
        # print(stop_times)
        # stop_times.to_csv(dir + "stop_times.csv)

        stops = pd.read_csv(dir + "stops.txt")
        stops['coordinate'] = [Point(-long, lat) for long, lat in
                   zip(stops['stop_lon'], stops['stop_lat'])]
        stops = stops[['stop_id', 'stop_name', 'stop_desc', 'zone_id', 'coordinate']]
        stops = gpd.GeoDataFrame(stops, geometry='coordinate')
        # print(stops)
        # stops.to_csv(dir + "stops.csv)

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
    income = pd.read_csv(TRACT_INC)
    income['Geography'] = income['Geography'].apply(lambda tract: tract.split(', ')[0])
    # print(shapes)
    # print(income)
    income = income.merge(right=shapes, how='left', left_on='Geography', right_on='NAMELSAD00')
    return gpd.GeoDataFrame(income)


def main():
    # county_pops = load_county_pop()
    # print(county_pops)
    # print(load_bus_data())
    load_tract_incomes()


if __name__ == '__main__':
    main()
