# MUNI Faculty Statistics Scraper

## Usage

### Fetch data for a faculty

- The internal faculty code (`1433`). _Obtain by selecting a faculty [here](https://is.muni.cz/studium/statistika), and
  then copying the value of the `fakulta` URL query parameter._

```shell
./fetch_stats.py 1433
```

#### ... to a CSV file

```shell
./fetch_stats.py 1433 > data.csv
```
