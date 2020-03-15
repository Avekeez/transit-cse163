import geopandas as gpd
import pandas as pd
import os
from shapely.geometry import Point
import matplotlib.pyplot as plt
import seaborn as sns

TRACT_SHP = 'data/tl_2010_53_tract00/tl_2010_53_tract00.shp'


def load_bus_data():
    """
    Reads from all gtfs data for metro+sound in 2013 and 2017, merging together
    geographical stop data and stop times.
    """
    gtfs = 'data/gtfs/'
    dirs = os.listdir(gtfs)
    complete = None
    for dir in dirs:
        tokens = dir.split('_')
        syst = tokens[0]
        year = int(tokens[1])

        dir = gtfs + dir + "/"

        stop_times = pd.read_csv(dir + "stop_times.txt")
        stop_times = stop_times[['trip_id', 'arrival_time',
                                 'departure_time', 'stop_id']]

        stops = pd.read_csv(dir + "stops.txt")
        stops['coordinate'] = [Point(long, lat) for long, lat in
                               zip(stops['stop_lon'], stops['stop_lat'])]
        stops = stops[['stop_id', 'stop_name', 'stop_desc',
                       'zone_id', 'coordinate']]

        merged_stops = stops.merge(right=stop_times, how='right',
                                   left_on='stop_id', right_on='stop_id')
        merged_stops['year'] = year
        merged_stops['system'] = syst

        if complete is None:
            complete = merged_stops
        else:
            complete = complete.append(merged_stops)
    return gpd.GeoDataFrame(complete, geometry='coordinate')


def load_tract_incomes():
    """
    Combines data for household incomes per tract in multiple counties,
    merging them with shape files for the tracts.
    """
    shapes = gpd.read_file(TRACT_SHP)
    inc_dirs = 'data/incomes/'
    dirs = os.listdir(inc_dirs)
    complete = None
    for dir in dirs:
        income = pd.read_csv(inc_dirs + dir)
        income['ID Geography'] = income['ID Geography'].apply(
            lambda tract: int(tract.split('US')[1]))
        if complete is None:
            complete = income
        else:
            complete = complete.append(income)
    complete = complete.merge(right=shapes, how='left',
                              left_on='ID Geography', right_on='CTIDFP00')
    return gpd.GeoDataFrame(complete)


def plot_income_change_over_availability(incomes, stops):
    """
    Creates a scatter plot of all census tracts, plotting their average incomes
    against their bus availability.
    """
    incomes_2017 = incomes[incomes['Year'] == 2017].dropna(subset=['geometry'])
    incomes_2013 = incomes[incomes['Year'] == 2013].dropna(subset=['geometry'])
    stops_2017 = stops[(stops['year'] == 2017)].dropna(subset=['coordinate'])

    covered_tracts = gpd.sjoin(incomes_2017, stops_2017,
                               how='inner', op='intersects')
    stops_per_tract = covered_tracts.groupby('ID Geography').size()

    incomes_2017 = incomes_2017[['Household Income by Race', 'ID Geography']]
    incomes_2017['income_2017'] = incomes_2017['Household Income by Race']
    incomes_2013 = incomes_2013[['Household Income by Race', 'ID Geography']]
    incomes_2013['income_2013'] = incomes_2013['Household Income by Race']

    d_incomes = incomes_2013.merge(right=incomes_2017,
                                   how='inner', on='ID Geography')
    d_incomes['delta'] = d_incomes['income_2017'] - d_incomes['income_2013']

    d_incomes = d_incomes.merge(right=stops_per_tract.rename('stops'),
                                how='inner', on='ID Geography')
    sns.regplot(data=d_incomes, x='stops', y='delta')

    plt.xlabel('Total # of bus visits to stops in the tract per week')
    plt.ylabel('Change in average household income in the tract')
    plt.ylim(-21000, 60000)
    plt.subplots_adjust(left=0.2)
    plt.title('Income Change vs Bus Availability')
    plt.savefig('income_change_over_availability.png')


def plot_buses_vs_income(bus_data, income_data):
    """
    Takes in the bus stop data and income data and creates a map between years
    """
    fig, [[ax1, ax2], [ax3, ax4]] = plt.subplots(2, figsize=(20, 10), ncols=2)
    income_data[income_data['Year'] == 2013].plot(
        ax=ax1, column='Household Income by Race', legend=True)
    bus_data[bus_data['year'] == 2013].plot(
        ax=ax1, marker='*', color='#000000', markersize=.001, alpha=0.5)
    income_data[income_data['Year'] == 2013].plot(
        ax=ax3,  column='Household Income by Race', legend=True)

    income_data[income_data['Year'] == 2017].plot(
        ax=ax2, column='Household Income by Race', legend=True)
    bus_data[bus_data['year'] == 2017].plot(
        ax=ax2, marker='*', color='#000000', markersize=.001, alpha=0.5)
    income_data[income_data['Year'] == 2017].plot(
        ax=ax4,  column='Household Income by Race', legend=True)
    ax1.set_title('2013 income, with bus stops')
    ax3.set_title('2013 income, without bus stops')
    ax2.set_title('2017 income, with bus stops')
    ax4.set_title('2017 income, without bus stops')
    fig.savefig("bus_vs_income.png")


def main():
    stops = load_bus_data()
    incomes = load_tract_incomes()
    plot_income_change_over_availability(incomes, stops)
    plot_buses_vs_income(stops, incomes)


if __name__ == '__main__':
    main()
