import csv
import json
import os
import urllib.request
import sys
from datetime import date, datetime, timedelta

DATE_FORMAT = '%Y/%m/%d'
CASE_DATA = 'RKI_COVID19.csv'
POP_DATA = 'einwohnerzahlen.csv'
AREA_DATA = 'landkreisflaechen.csv'


def main():
    format = True if "--format" in sys.argv else False
    download = False if "--no-download" in sys.argv else True

    if download:
        download_case_data()

    d, c = parse_case_data()
    add_missing_counties(c)
    parse_population_data(c)
    parse_area_data(c)

    if download:
        os.remove(CASE_DATA)

    sum_up_total_population_and_area(c)
    calculate_population_density(c)

    pad_data_set(d, c)
    aggregate_daily_data(d, c)
    assemble_nationwide_data(d, c)
    handle_special_cases(d, c)
    compute_incidences(d, c)

    write_to_file(d, "data.json", format)
    write_to_file(c, "counties.json", format)
    print("DONE")


def download_case_data():
    print("Downloading case data")

    url = "https://www.arcgis.com/sharing/rest/content/items/f10774f1c63e40168479a1feb6c7ca74/data"
    urllib.request.urlretrieve(url, CASE_DATA)


def parse_case_data():
    print("Parsing case data file")

    data = {}
    counties = {}

    with open(CASE_DATA, newline='', encoding='ISO-8859-1') as csv_file:
        reader = csv.reader(csv_file)
        first_row = True

        for row in reader:
            if first_row:
                first_row = False
                index_date = row.index("Meldedatum")
                index_county_id = row.index("IdLandkreis")
                index_county_name = row.index("Landkreis")
                index_new_cases = row.index("AnzahlFall")
                index_new_deaths = row.index("AnzahlTodesfall")

            else:
                date = row[index_date].split()[0]
                county_id = row[index_county_id]

                if date not in data:
                    data[date] = {}

                if county_id not in data[date]:
                    data[date][county_id] = create_empty_element()

                if county_id not in counties:
                    counties[county_id] = {
                        "name": row[index_county_name],
                        "population": None,
                        "area": None,
                        "density": None
                    }

                elem = data[date][county_id]
                elem["newCases"] += int(row[index_new_cases])
                elem["newDeaths"] += int(row[index_new_deaths])

        return data, counties


def create_empty_element():
    return {
        "newCases": 0,
        "newDeaths": 0,
        "freeBeds": None,
        "occupiedBeds": None,
        "reserveBeds": None,
        "totalCases": None,
        "totalDeaths": None,
        "caseIncidence": None,
        "deathIncidence": None
    }


def add_missing_counties(counties):
    counties["11000"] = {
        "name": "Berlin",
        "population": None,
        "area": None,
        "density": None
    }


def parse_population_data(counties):
    print("Parsing population data file")

    with open(POP_DATA, newline='', encoding='ISO-8859-1') as csv_file:
        reader = csv.reader(csv_file,  delimiter=';')
        row_count = 0

        for row in reader:
            row_count += 1
            if 6 < row_count < 483:
                if row[0] in counties:
                    if counties[row[0]]["population"] is None:
                        counties[row[0]]["population"] = int(row[2])
                    else:
                        print(f"WARNING: Multiple population entries for {row[0]}, '{row[1]}'!")


def parse_area_data(counties):
    print("Parsing area data file")

    with open(AREA_DATA, newline='', encoding='ISO-8859-1') as csv_file:
        reader = csv.reader(csv_file,  delimiter=';')
        row_count = 0

        for row in reader:
            row_count += 1
            if 6 < row_count < 483:
                if row[0] in counties:
                    if counties[row[0]]["area"] is None:
                        counties[row[0]]["area"] = float(row[2].replace(',', '.'))
                    else:
                        print(f"WARNING: Multiple area entries for {row[0]}, '{row[1]}'!")


def sum_up_total_population_and_area(counties):
    print("Summing up total population and area values")

    all = {
        "name": "Deutschland",
        "population": 0,
        "area": 0,
        "density": None
    }

    for c in counties.values():
        if c["population"]:
            all["population"] += c["population"]

        if c["area"]:
            all["area"] += c["area"]

    counties["all"] = all


def calculate_population_density(counties):
    for c in counties.values():
        if c["population"] is not None and c["area"]:
            c["density"] = c["population"] / c["area"]


def pad_data_set(data, counties):
    print("Padding data set with empty data points")

    sorted_dates = sorted(list(data))
    date = datetime.strptime(sorted_dates[0], DATE_FORMAT).date()
    last_date = datetime.strptime(sorted_dates[-1], DATE_FORMAT).date()
    delta = timedelta(days=1)

    while date <= last_date:
        id = date.strftime(DATE_FORMAT)
        if id not in data:
            data[id] = {}
        date += delta

    for d in data:
        for c in counties:
            if c not in data[d]:
                data[d][c] = create_empty_element()


def aggregate_daily_data(data, counties):
    print("Aggregating total infection cases and deaths")

    sorted_dates = sorted(list(data))

    for c in counties:
        total_cases = 0
        total_deaths = 0

        for date in sorted_dates:
            elem = data[date][c]

            if elem["newCases"]:
                total_cases += elem["newCases"]
            elem["totalCases"] = total_cases

            if elem["newDeaths"]:
                total_deaths += elem["newDeaths"]
            elem["totalDeaths"] = total_deaths


def assemble_nationwide_data(data, counties):
    print("Assembling nationwide data")

    for date in data.values():
        all = create_empty_element()
        all["totalCases"] = 0
        all["totalDeaths"] = 0

        for c in counties:
            all["newCases"] += date[c]["newCases"]
            all["newDeaths"] += date[c]["newDeaths"]
            all["totalCases"] += date[c]["totalCases"]
            all["totalDeaths"] += date[c]["totalDeaths"]

        date["all"] = all


def handle_special_cases(data, counties):
    print("Handling special cases")

    # Berlin
    districts = ["11001", "11002", "11003", "11004", "11005", "11006",
                 "11007", "11008", "11009", "11010", "11011", "11012"]

    for d in data.values():
        for dis in districts:
            d["11000"]["newCases"] += d[dis]["newCases"]
            d["11000"]["newDeaths"] += d[dis]["newDeaths"]
            d["11000"]["totalCases"] += d[dis]["totalCases"]
            d["11000"]["totalDeaths"] += d[dis]["totalDeaths"]


def compute_incidences(data, counties):
    print("Computing seven day incidences")

    for d in data:
        date = datetime.strptime(d, DATE_FORMAT).date()

        for c in counties:
            data[d][c]["caseIncidence"] = data[d][c]["newCases"]
            data[d][c]["deathIncidence"] = data[d][c]["newDeaths"]

            for i in range(1, 7):
                day = (date - timedelta(days=i)).strftime(DATE_FORMAT)
                if day in data:
                    data[d][c]["caseIncidence"] += data[day][c]["newCases"]
                    data[d][c]["deathIncidence"] += data[day][c]["newDeaths"]

            if counties[c]["population"]:
                data[d][c]["caseIncidence"] *= 100000
                data[d][c]["caseIncidence"] /= counties[c]["population"]
            else:
                data[d][c]["caseIncidence"] = None

            if counties[c]["population"]:
                data[d][c]["deathIncidence"] *= 100000
                data[d][c]["deathIncidence"] /= counties[c]["population"]
            else:
                data[d][c]["deathIncidence"] = None


def write_to_file(content, filename, format=False):
    print(f"Writing data to '{filename}'")

    with open(filename, 'w') as file:
        if format:
            json.dump(content, file, indent=4, sort_keys=True)
        else:
            json.dump(content, file, separators=(',', ':'), sort_keys=True)


if __name__ == "__main__":
    main()
