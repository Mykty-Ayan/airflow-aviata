import datetime
import requests
import xmltodict

from src.reqresp import national_bank


class NationalBankClient:
    def get_exchange_rates(self, to_date=datetime.date.today()) -> national_bank.NationalBankRate:
        request_url = f"{self.base_url}?fdate={to_date.strftime('%d.%m.%Y')}"
        print(f"Requesting URL: {request_url}")

        response = requests.get(request_url)
        if response.status_code == 200:
            response_data = response.text
            data = parse_national_bank_rate(response_data)
            return data
        else:
            response.raise_for_status()

    def convert_currency(self, amount, from_currency, to_currency):
        # Implementation to convert currency using fetched exchange rates
        pass


    def __init__(self, config):
        self.base_url = config.get("NATIONAL_BANK_API_URL", "https://nationalbank.kz/rss/get_rates.cfm")
        self.exchange_rates = None  # Don't fetch on initialization to avoid delays


def parse_national_bank_rate(text: str) -> national_bank.NationalBankResponse:
    data = xmltodict.parse(text)
    rate = data.get("rates", {}) 
    currencies = [national_bank.NationalBankCurrency(full_name=currency.get("fullname", "").title(),
                                                      title=currency.get("title", ""),
                                                      description=currency.get("description", ""),
                                                      quantity=int(currency.get("quantity", 0)),
                                                      index=currency.get("index", ""),
                                                      change=float(currency.get("change", 0)))
                  for currency in rate.get("item", [])]
    data["currencies"] = currencies
    rates = national_bank.NationalBankRate(
        generator=rate.get("generator", ""),
        title=rate.get("title", ""),
        description=rate.get("description", ""),
        copyright=rate.get("copyright", ""),
        date=rate.get("date", ""),
        currencies=currencies
    )
    return national_bank.NationalBankResponse(rate=rates)