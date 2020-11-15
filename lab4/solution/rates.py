from enum import Enum
from datetime import date, timedelta, datetime

import requests
import matplotlib.pyplot as plt
import matplotlib.dates as dt
import pandas as pd


MAX_DAYS = 365
AVG_TABLE_TYPE = "A"
DATE_FORMAT = "%Y-%m-%d"
API_URL = "http://api.nbp.pl/api"


class Currency(Enum):
    USD = "USD"
    EURO = "EUR"


def get_date_ranges(days_num):
    if days_num <= 0:
        raise ValueError("Number of days cannot be <= 0")

    today = date.today()
    dates = []

    if days_num <= MAX_DAYS:
        start = today - timedelta(days=days_num - 1)
        dates.append((start, today))
    else:
        current_delta = timedelta(days=MAX_DAYS - 1)
        one_delta = timedelta(days=1)

        current_end = today
        while True:
            current_start = current_end - current_delta

            start = current_start
            end = current_end
            dates.append((start, end))

            days_num -= current_delta.days + 1
            if days_num <= 0:
                break

            current_end = current_start - one_delta

            if days_num < MAX_DAYS:
                current_delta = timedelta(days=days_num - 1)

    dates.reverse()
    return dates


def checked_request_json(url):
    response = requests.get(url)

    if response.status_code != 200:
        print(
            f"Status code '{response.status_code}' when connecting to '{url}'",
            f"Reponse text: '{response.text}'",
            sep="\n"
        )
        return {}

    return response.json()


def daily_exchange_rates_for(currency, days_num=1):
    dates = get_date_ranges(days_num)
    dateless_url = f"{API_URL}/exchangerates/rates/{AVG_TABLE_TYPE}/{currency.value}"

    exchange_rates = []

    for date_ in dates:
        start = date_[0].strftime(DATE_FORMAT)
        end = date_[1].strftime(DATE_FORMAT)

        url = f"{dateless_url}/{start}/{end}"
        response_json = checked_request_json(url)

        if response_json:
            days = response_json["rates"]
            for day in days:
                exchange_rates.append({
                    "date": datetime.strptime(day["effectiveDate"], DATE_FORMAT).date(),
                    "rate": day["mid"]
                })

    return exchange_rates


def draw_chart_for_rates_of(currency1, name1, currency2, name2):
    if not currency1 or not currency2:
        raise ValueError("Some of the currency data lists are empty")

    df1 = pd.DataFrame(currency1)
    df2 = pd.DataFrame(currency2)

    plt.gca().xaxis.set_major_formatter(dt.DateFormatter(DATE_FORMAT))

    plt.plot(df1["date"], df1["rate"], label=name1)
    plt.plot(df2["date"], df2["rate"], label=name2)
    plt.gcf().autofmt_xdate()

    plt.title(f"{name1} and {name2} average exchange rate over time")
    plt.xlabel("Date [YYYY-MM-DD]")
    plt.ylabel("Exchange rate [PLN]")
    plt.tight_layout()

    plt.margins(0, None)
    plt.legend()

    plt.savefig(f"{name1.replace(' ', '_')}_{name2.replace(' ', '_')}_plot.svg")


if __name__ == "__main__":
    half_year_in_days = 366 // 2
    usd = daily_exchange_rates_for(Currency.USD, half_year_in_days)
    euro = daily_exchange_rates_for(Currency.EURO, half_year_in_days)

    draw_chart_for_rates_of(usd, Currency.USD.value, euro, Currency.EURO.value)
