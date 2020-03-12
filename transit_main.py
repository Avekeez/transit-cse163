import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point, Polygon

COUNTY_SHP = 'data/cb_2018_53_cousub_500k/cb_2018_53_cousub_500k.shp'
COUNTY_POP = 'data/cc-est2018-alldata-53.csv'


def read_shapes(shapes_txt):
    df = pd.read_csv(shapes_txt)
    df['point'] = [Point(-long, lat) for long, lat in
                   zip(df['shape_pt_lon'], df['shape_pt_lat'])]
    shapes = df.groupby('shape_id')['point'].apply(
        lambda points: Polygon([[p.x, p.y] for p in points]))
    df = df.drop_duplicates('shape_id')
    df = df.drop(['shape_pt_sequence', 'shape_pt_lat',
                  'shape_pt_lon', 'point'], axis=1)
    df['geometry'] = shapes.values
    return gpd.GeoDataFrame(df)


def load_bus_data():
    gtfs = 'data/gtfs/'
    dirs = os.listdir(gtfs)
    for dir in dirs:
        tokens = dir.split('_')
        syst = tokens[0]
        year = tokens[1]

        dir = gtfs + dir + "/"

        shapes = read_shapes(dir + "shapes.txt")
        # shapes.to_csv("shapes_csv.")

        trips = pd.read_csv(dir + "trips.txt")
        # trips.to_csv("trips.csv")

        stop_times = pd.read_csv(dir + "stop_times.txt")
        # stop_times.to_csv(dir + "stop_times.csv)

        stops = pd.read_csv(dir + "stops.txt")
        # stops.to_csv(dir + "stops.csv)

        # subdf = shapes.merge(trips, left_on='shape_id', right_on='shape_id', how='outer')
        # subdf = subdf.merge(stop_times, left_on='trip_id', right_on='trip_id', how='outer')
        # subdf = subdf.merge(stops, left_on='stop_id', right_on='stop_id', how='outer')
        # subdf = subdf.dropna()


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


def main():
    # county_pops = load_county_pop()
    # print(county_pops)
    load_bus_data()


if __name__ == '__main__':
    main()
