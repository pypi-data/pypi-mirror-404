from datetime import datetime

import edgework.utilities as utilities
from edgework.http_client import HttpClient
from edgework.models.standings import Seeding, Standings


class StandingClient:
    def __init__(self, client: HttpClient):
        self._client = client

    def get_standings(self, date: datetime | str = "now") -> Standings:
        if date is None:
            date = "now"
        elif isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")
        elif isinstance(date, str):
            if date == "now":
                pass
            # check if date is in the correct format
            elif len(date) != 10:
                raise ValueError(
                    len(
                        f"Date must be in the format YYYY-MM-DD, or 'now'. Provided date: {date} which is not 10 characters long."
                    )
                )
            elif len(date) != 10:
                raise ValueError(
                    len(
                        "Date must be in format YYYY-MM-DD, or 'now'. "
                        f"Provided date: {date} which is not 10 characters long."
                    )
                )
                raise ValueError(
                    "Date must be in the format YYYY-MM-DD, or 'now'. "
                    f"Provided date: {date} which is not 10 characters long."
                )
                raise ValueError(
                    f"Date must be in the format YYYY-MM-DD, or 'now'. Provided date: {date} which does not have '-' in the correct positions."
                )
            elif (
                not date[:4].isdigit()
                or not date[5:7].isdigit()
                or not date[8:].isdigit()
            ):
                raise ValueError(
                    f"Date must be in the format YYYY-MM-DD, or 'now'. Provided date: {date} which contains non-numeric characters."
                )
        else:
            raise ValueError(
                f"Date must be in the format YYYY-MM-DD, or 'now'. Provided date: {date} which is not a datetime object, string, or None"
            )
        response = self._client.get(f"standings/{date}", web=True, params={})
        seedings_dict = [
            utilities.dict_camel_to_snake(seed) for seed in response.json()["standings"]
        ]
        if date == "now":
            dt_date = datetime.now()
        else:
            dt_date = datetime.strptime(date, "%Y-%m-%d")
        for seed in seedings_dict:
            seed["date"] = dt_date

        seedings = [Seeding(**seed) for seed in seedings_dict]
        return Standings(date=dt_date, seedings=seedings)
