import logging
import os
from datetime import date, timedelta
from typing import Dict, List

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

API_BASE_URL = "https://api-school.kinderlime.com/api"
EMAIL = os.getenv("AUTH_EMAIL")
PASSWORD = os.getenv("AUTH_PASSWORD")


def authenticate(email: str, password: str) -> Dict[str, any]:
    logger.info("authenticating with api")
    response = requests.post(
        url=f"{API_BASE_URL}/web/auth/",
        json={
            "email": email,
            "password": password,
        },
    )

    if response.status_code != 201:
        raise Exception(f"authentication response status code not as expected :: {response.status_code}")

    return response.json()


def get_kids(authentication_token) -> List[Dict[str, any]]:
    logger.info("getting kids...")
    response = requests.get(
        url=f"{API_BASE_URL}/web/parent/kids/",
        headers={
            "authorization": f"Bearer {authentication_token}",
        },
    )

    if response.status_code != 200:
        raise Exception(f"get kids response status code not as expected :: {response.status_code}")

    kids = response.json()["kids"]
    logger.info("found %d kids", len(kids))

    return kids


def get_daily_activities(kid, authentication_token):
    logger.info("getting daily activities for kid %s", kid["name"])

    daily_activities = []
    has_more = True
    current_page = 1

    while has_more:
        logger.info("getting page %d of daily activities...", current_page)

        response = requests.get(
            url=f"{API_BASE_URL}/web/parent/daily_activities/",
            headers={
                "authorization": f"Bearer {authentication_token}",
            },
            params={
                "kid_id": kid["id"],
                # "filters[daily_activity][date_from]": date.today().isoformat(),
                "page": current_page
            },
        )

        if response.status_code != 200:
            raise Exception(f"get daily activity response status code not as expected :: {response.status_code}")

        activities = response.json()["daily_activities"]
        current_page += 1
        has_more = len(activities) > 0
        daily_activities.extend(activities)

    logger.info("got %d dailiy activities", len(daily_activities))
    return daily_activities


def download_photos(daily_activities: List[Dict[str, any]]):
    photo_urls = [activity["photo_url"] for activity in daily_activities if activity["photo_url"] is not None]
    logger.info("downloading %d photos...", len(photo_urls))

    for index, url in enumerate(photo_urls):
        response = requests.get(
            url=url,
        )

        with open(f"photos/photo-{index}.jpg", "wb") as file:
            file.write(response.content)


def handler(event=None, context=None):
    authentication = authenticate(EMAIL, PASSWORD)
    authentication_token = authentication["user"]["auth_token"]

    kids = get_kids(authentication_token)
    oscar = next(kid for kid in kids if kid["name"] == "Oscar Loes")

    daily_activities = get_daily_activities(oscar, authentication_token)
    download_photos(daily_activities)

    logger.info("done")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    handler()
