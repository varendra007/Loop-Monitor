from threading import Thread
from random import randint
from typing import List, Dict, Tuple
from datetime import datetime
import pandas as pd
from config.client import db
from config.constants import HARD_CODE_TIME
from service.utils import TimeUtils
from datetime import time


class Database:
    def __init__(self, status_path: str, timezone_path: str, hours_path: str) -> None:
        self.status = pd.read_csv(status_path)
        self.timezone = pd.read_csv(timezone_path)
        self.hours = pd.read_csv(hours_path)
        self.collections = ["status", "timezone", "hours"]
        self.date_format = "%Y-%m-%d %H:%M:%S.%f"
        self.current_time = datetime.strptime(HARD_CODE_TIME, self.date_format)
        self.time_utils = TimeUtils(self.date_format)

    def migrate(self) -> None:
        existing_collections = db.list_collection_names()

        for collection in self.collections:
            if collection not in existing_collections:
                df = getattr(self, collection)
                df["store_id"] = df["store_id"].astype(str)
                df_dict = df.to_dict("records")
                db[collection].insert_many(df_dict)
            else:
                print(f"Collection {collection} already exists.")

    def get_business_hours_weekly(self, store_id: str) -> Dict:
        business_hours = {}

        for day in range(7):
            hours_data = self.get_business_hours(store_id, day)
            business_hours[day] = hours_data

        return business_hours

    def get_unique_stores(self) -> List:
        unique_stores = db.status.distinct("store_id")

        return unique_stores

    def interpolate_and_calculate(self, observations, business_hours_per_day):
        observations.sort(key=lambda x: x["timestamp_utc"])

        uptime = 0
        downtime = 0

        for day, business_hours in business_hours_per_day.items():
            day = int(day)
            day_observations = [
                obs for obs in observations if obs["timestamp_utc"].weekday() == day
            ]

            if len(day_observations) == 0:
                continue

            for time_range in business_hours:
                business_start = time.fromisoformat(time_range["start_time_local"])
                business_end = time.fromisoformat(time_range["end_time_local"])

                business_start_utc = datetime.combine(
                    day_observations[0]["timestamp_utc"].date(), business_start
                )
                business_end_utc = datetime.combine(
                    day_observations[0]["timestamp_utc"].date(), business_end
                )

                current_time = business_start_utc

                for i in range(len(day_observations) - 1):
                    t1, s1 = (
                        day_observations[i]["timestamp_utc"],
                        day_observations[i]["status"],
                    )
                    t2, s2 = (
                        day_observations[i + 1]["timestamp_utc"],
                        day_observations[i + 1]["status"],
                    )

                    if t1 < business_start_utc or t2 > business_end_utc:
                        continue

                    mid_point = t1 + (t2 - t1) / 2

                    if s1 == "active":
                        uptime += (mid_point - current_time).seconds / 60
                    else:
                        downtime += (mid_point - current_time).seconds / 60

                    current_time = mid_point

                if day_observations[-1]["timestamp_utc"] <= business_end_utc:
                    if day_observations[-1]["status"] == "active":
                        uptime += (business_end_utc - current_time).seconds / 60
                    else:
                        downtime += (business_end_utc - current_time).seconds / 60

        return uptime, downtime

    def get_time_zone(self, store_id: str) -> str:
        timezone_data = db.timezone.find_one({"store_id": store_id})
        if not timezone_data:
            timezone = "America/Chicago"
        else:
            timezone = timezone_data["timezone_str"]
        return timezone

    def get_business_hours(self, store_id: str, day: int):
        hours_data = list(
            db.hours.find(
                {"store_id": store_id, "day": day}, {"_id": 0, "store_id": 0, "day": 0}
            )
        )

        return hours_data

    def check_business_hours(self, store_id: str, timestamp: str) -> bool:
        day = self.time_utils.extract_day(timestamp)
        hours_data = self.get_business_hours(store_id, day)
        if not hours_data:
            return True

        is_business = False

        for hour_data in hours_data:
            start_time_local = hour_data["start_time_local"]
            end_time_local = hour_data["end_time_local"]
            is_business = is_business or self.time_utils.is_in_range(
                start_time_local, end_time_local, timestamp
            )

        return is_business

    def get_store_interval_data(self, store_id: str, range_hours: int) -> List[Dict]:
        start_time = self.current_time - pd.Timedelta(hours=range_hours)
        start_time = str(start_time)
        query = {
            "store_id": store_id,
            "timestamp_utc": {"$gte": start_time},
        }
        timezone = self.get_time_zone(store_id)
        store_status = list(db.status.find(query, {"_id": 0, "store_id": 0}))

        for store in store_status:
            store["timestamp_utc"] = " ".join(store["timestamp_utc"].split(" ")[:2])
            store["timestamp_utc"] = datetime.strptime(
                self.time_utils.convert_to_local(store["timestamp_utc"], timezone),
                self.date_format,
            )

        return store_status

    def get_last_hour_report(self, shop_id: str) -> Tuple:
        observations = self.get_store_interval_data(shop_id, 1)

        buisness_count = 0
        inactive_count = 0
        for observation in observations:
            if self.check_business_hours(shop_id, str(observation["timestamp_utc"])):
                if observation["status"] == "active":
                    buisness_count += 1
                else:
                    inactive_count += 1

        if buisness_count == 0 and inactive_count == 0:
            return 0, 0

        total = buisness_count + inactive_count

        return 60 * buisness_count / total, 60 * inactive_count / total

    def get_last_day_report(self, shop_id: str) -> Tuple:
        day = self.current_time.weekday()
        business_hours = self.get_business_hours(shop_id, day - 1)
        observations = self.get_store_interval_data(shop_id, 24)
        uptime, downtime = self.interpolate_and_calculate(
            observations=observations,
            business_hours_per_day={day: business_hours},
        )

        return uptime / 60, downtime / 60

    def get_last_week_report(self, shop_id: str) -> Tuple:
        business_hours = self.get_business_hours_weekly(shop_id)
        observations = self.get_store_interval_data(shop_id, 168)
        uptime, downtime = self.interpolate_and_calculate(
            observations=observations,
            business_hours_per_day=business_hours,
        )

        return uptime / 60, downtime / 60

    def create_and_upload_report(self, report_id: str) -> None:
        unique_stores = self.get_unique_stores()
        for store in unique_stores:
            last_hour_report = self.get_last_hour_report(store)
            last_day_report = self.get_last_day_report(store)
            last_week_report = self.get_last_week_report(store)
            uptime_last_hour, downtime_last_hour = last_hour_report
            uptime_last_day, downtime_last_day = last_day_report
            uptime_last_week, downtime_last_week = last_week_report
            new_data = {
                "store_id": store,
                "uptime_last_hour": "%.2f" % uptime_last_hour,
                "uptime_last_day": "%.2f" % uptime_last_day,
                "uptime_last_week": "%.2f" % uptime_last_week,
                "downtime_last_hour": "%.2f" % downtime_last_hour,
                "downtime_last_day": "%.2f" % downtime_last_day,
                "downtime_last_week": "%.2f" % downtime_last_week,
            }
            db.reports.update_one(
                {"report_id": report_id}, {"$push": {"data": new_data}}
            )

        db.reports.update_one(
            {"report_id": report_id}, {"$set": {"status": "complete"}}
        )

    def trigger_report(self):
        new_report_id = str(randint(10000000, 99999999))
        db.reports.insert_one(
            {"report_id": new_report_id, "status": "progress", "data": []}
        )
        thread = Thread(target=self.create_and_upload_report, args=(new_report_id,))
        thread.start()

        return new_report_id

    def get_report_from_id(self, report_id: str):
        return db.reports.find_one({"report_id": report_id})
