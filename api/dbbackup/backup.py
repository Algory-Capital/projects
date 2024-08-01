import pymongo
from dotenv import load_dotenv
import os
import json
from bson import json_util
from datetime import datetime

# CWD must be api

load_dotenv()

mongoURL = os.getenv("MONGO_CLIENT")

client = pymongo.MongoClient(mongoURL)

aum_collection = client["algoryPortDB"]["aumdatas"]
equities_collection = client["algoryPortDB"]["equities"]


def parse_json(data):
    return json.loads(json_util.dumps(data))


def equities_to_json(path="equities.json",timestr = "NONE"):
    data = {}

    for i in equities_collection.find():
        data[i["ticker"]] = parse_json(i)

    with open(os.path.join("dbbackup/Data", f"{path}:{timestr}"), "w") as f:
        json.dump(data, f)


def aum_to_json(path="aum.json", timestr = "NONE"):

    for i in aum_collection.find():
        data = parse_json(i)

    with open(os.path.join("dbbackup/Data", f"{path}:{timestr}"), "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    now = datetime.now()
    timestr = now.strftime("%m/%d/%Y, %H:%M:%S")

    equities_to_json(timestr=timestr)
    aum_to_json(timestr = timestr)
