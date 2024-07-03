import pymongo
from dotenv import load_dotenv
import os
import json
from bson import json_util

# CWD must be api

load_dotenv()

mongoURL = os.getenv("MONGO_CLIENT")

client = pymongo.MongoClient(mongoURL)

aum_collection = client["algoryPortDB"]["aumdatas"]
equities_collection = client["algoryPortDB"]["equities"]


def parse_json(data):
    return json.loads(json_util.dumps(data))


def equities_to_json(path="equities.json"):
    data = {}

    for i in equities_collection.find():
        data[i["ticker"]] = parse_json(i)

    with open(os.path.join("dbbackup/Data", path), "w") as f:
        json.dump(data, f)


def aum_to_json(path="aum.json"):

    for i in aum_collection.find():
        data = parse_json(i)

    with open(os.path.join("dbbackup/Data", path), "w") as f:
        json.dump(data, f)


if __name__ == "__main__":
    equities_to_json()
    aum_to_json()
