import paho.mqtt.client as mqtt
from datetime import datetime
import time, pytz
import json
import argparse
import logging, logging.handlers
import os

logFilename = os.getenv('LOG_FILENAME', '/var/log/app/mocksunnyislanddatacollector.out')

logger = logging.getLogger(__name__)
handler = logging.handlers.RotatingFileHandler(logFilename, maxBytes=524288, backupCount=5)

formatter = logging.Formatter(
    '%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(int(os.getenv("LOG_LEVEL", logging.INFO)))

testJsonFile = open('./mock_sunnyisland_data.json','r')
testJsonString = testJsonFile.read()
testJsonFile.close()
testJsonData = json.loads(testJsonString)

parser = argparse.ArgumentParser(description="Mock Sunny Island Data Publisher")
parser.add_argument("--mqtthost",help="The hostname of the MQTT server", default="localhost")
parser.add_argument("--mqttport",help="The port of the MQTT server", type=int, default=1883)
parser.add_argument("--mqtttopic",help="The topic the SI data is published to", required=True)
args = parser.parse_args()

def main():

    client = mqtt.Client()
    logger.info("Starting mocksunnyislanddatapublisher")
    while(True):
        try:
            now = pytz.UTC.localize(datetime.utcnow())
            logger.info(f'Publishing mock data to topic {args.mqtttopic}')
            testJsonData["time"] = round(now.timestamp())
            client.connect(args.mqtthost, args.mqttport, 60)
            client.publish(args.mqtttopic, json.dumps(testJsonData))
            client.disconnect()
            time.sleep(15)
        except:
            logging.error("Error publishing mock data", exc_info=1)
            return -1


if __name__ == "__main__":
    main()
