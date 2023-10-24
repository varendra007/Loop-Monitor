# Loop-Monitor

Tech Framework: FastAPI Framework

To run the service

1. Install the dependencies by running the following commands:

```bash
pip install -r requirements.txt
```

2. To run the server:

```bash
uvicorn main:app --reload
```

3. Open `http://127.0.0.1:8000/docs#/` on browser to access the APIs.

**Note:** Current time is hardcoded in the `.env` file to match with the timings of provided data

`data/` contains the given csv files which is being used to monitor the stores.

Here is the sample video link of the working of the server.
[Video](https://drive.google.com/file/d/1RIc3U2TJjOcGS58isnv18axX-SFxGSwb/view?usp=sharing)

## Contents of env file

```
MONGO_URL="mongodb+srv://admin:qJf6s9PHqftrJHwD@cluster0.umfdbyo.mongodb.net/?retryWrites=true&w=majority"
STATUS_PATH="./data/status.csv"
TIMEZONE_PATH="./data/timezone.csv"
HOURS_PATH="./data/hours.csv"
PING_PERIOD_MINS="60"
HARD_CODE_TIME="2023-01-25 18:13:22.47922"
```
