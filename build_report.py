import pathlib
import sys
import csv
import dataclasses
from typing import Dict, Optional
from datetime import date, timedelta
import requests
from jinja2 import Environment, FileSystemLoader, select_autoescape


@dataclasses.dataclass
class Contagion:
    contagions: int
    tests: int
    report_date: date

    @property
    def percents(self) -> float:
        return 100 * self.contagions / self.tests


def datetime_format(value, format="%d-%m-%Y"):
    return value.strftime(format)


def format_currency(value):
    return "{:,.2f}".format(value).replace('.00', '').replace(',', '.')


def format_percent(value):
    return "{:,.2f}".format(value)


csv_dt_pattern = "%Y-%m-%dT17:00:00"


def _diff_data(ref_date: date = date.today()) -> Optional[Contagion]:
    delta = timedelta(days=1)
    before_date = ref_date - delta
    csv_url = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv"

    resp = requests.get(csv_url)
    if resp.ok:
        decoded_content = resp.content.decode('utf-8')
        data = csv.reader(decoded_content.splitlines(),
                          delimiter=',')  # TODO cache

        rows = list(filter(lambda r:
                           r[0] == ref_date.strftime(csv_dt_pattern) or r[0] == before_date.strftime(csv_dt_pattern), data))

        #print(f"rows {list(rows)}")
        if len(rows) == 2:
            return Contagion(report_date=ref_date, contagions=int(rows[1][8]), tests=int(rows[1][14]) - int(rows[0][14]))
        else:
            print(rows)
            return None

    else:
        return None


def main(template_name: str = 'index.html', output_dir: str = 'build') -> int:

    latest_data = _diff_data()  # date.today() - timedelta(days=1)
    if latest_data:
        previous_data = [_diff_data(
            date.today() - timedelta(days=x)) for x in range(1, 7)]

        template_path = pathlib.Path().absolute()

        env = Environment(
            loader=FileSystemLoader(template_path),
            autoescape=select_autoescape(['html', 'xml'])
        )
        env.filters['datetimeformat'] = datetime_format
        env.filters['currencyformat'] = format_currency
        env.filters['percentformat'] = format_percent
        template = env.get_template(template_name)
        output_from_parsed_template = template.render(
            latest_data=latest_data, previous_data=previous_data)
        with open(output_dir + "/" + template_name, "w") as fh:
            fh.write(output_from_parsed_template)
        return 0
    else:
        return -1


if __name__ == "__main__":
    return_code = main()
    sys.exit(return_code)
