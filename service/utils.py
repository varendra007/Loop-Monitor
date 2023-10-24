from datetime import datetime
import pytz


class TimeUtils:
    def __init__(self, timestamp_format) -> None:
        self.format = timestamp_format

    def extract_day(self, timestamp: str) -> int:
        timestamp = datetime.strptime(timestamp, self.format)
        day_of_week = timestamp.weekday()
        return day_of_week

    def convert_to_local(self, timestamp: str, timezone: str) -> str:
        timestamp = datetime.strptime(timestamp, self.format)
        target_timezone = pytz.timezone(timezone)
        timestamp = timestamp.replace(tzinfo=pytz.UTC).astimezone(target_timezone)
        timestamp = timestamp.strftime(self.format)
        return timestamp

    def is_in_range(self, start_hour: str, end_hour: str, timestamp: str) -> bool:
        hour = datetime.strptime(timestamp.split(" ")[1], "%H:%M:%S.%f")
        start_hour = datetime.strptime(start_hour, "%H:%M:%S")
        end_hour = datetime.strptime(end_hour, "%H:%M:%S")
        return start_hour <= hour <= end_hour
