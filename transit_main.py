import geopandas as gpd
import pandas as pd

COUNTY_SHP = 'data/cb_2018_53_cousub_500k/cb_2018_53_cousub_500k.shp'
COUNTY_POP = 'data/cc-est2018-alldata-53.csv'


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
    county_pops = load_county_pop()
    print(county_pops)


if __name__ == '__main__':
    main()
