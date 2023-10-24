import pandas as pd
from starlette.responses import Response
from fastapi import FastAPI, HTTPException, status
from config.constants import STATUS_PATH, TIMEZONE_PATH, HOURS_PATH
from service.database import Database


app = FastAPI()
paths = [STATUS_PATH, TIMEZONE_PATH, HOURS_PATH]
database = Database(*paths)


@app.on_event("startup")
async def startup_event():
    database.migrate()


@app.post("/")
async def root():
    return {"message": "Hello World"}


@app.post("/trigger_report")
async def trigger_report_creation():
    report_id = database.trigger_report()
    return {"Report ID": report_id}


@app.get("/get_report/{report_id}")
async def get_report(report_id: str):
    report_data = database.get_report_from_id(report_id)
    if not report_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not Generated"
        )

    if report_data["status"] == "progress":
        return {"Status": "Running"}
    report_list = report_data["data"]
    df = pd.DataFrame(report_list)
    csv_filename = f"report_{report_id}.csv"
    csv_headers = [
        "store_id",
        "uptime_last_hour (minutes)",
        "uptime_last_day (hours)",
        "uptime_last_week (hours)",
        "downtime_last_hour (minutes)",
        "downtime_last_day (hours)",
        "downtime_last_week (hours)",
    ]
    csv_content = df.to_csv(index=False, header=csv_headers, sep=",")
    response = Response(content=csv_content)
    response.headers["Content-Disposition"] = f'attachment; filename="{csv_filename}"'
    response.media_type = "text/csv"
    return response
