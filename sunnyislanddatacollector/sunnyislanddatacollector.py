import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from datetime import datetime
import argparse
import logging, logging.handlers, os
import json
import redis

logFilename = os.getenv('LOG_FILENAME', '/var/log/app/sunnyislanddatacollector.out')

logger = logging.getLogger(__name__)
handler = logging.handlers.RotatingFileHandler(logFilename, maxBytes=524288, backupCount=5)

formatter = logging.Formatter(
    '%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(int(os.getenv("LOG_LEVEL", logging.INFO)))

parser = argparse.ArgumentParser(description="SMA Sunny Island Data Collection Shell")
parser.add_argument("--mqtthost",help="The hostname of the MQTT server", default="localhost")
parser.add_argument("--mqttport",help="The port of the MQTT server", type=int, default=1883)
parser.add_argument("--mqtttopic",help="The topic the SI data is published to", required=True)
parser.add_argument("--influxdbhost",help="The hostname of InfluxDb", required=True)
parser.add_argument("--influxdbtoken",help="The API token for InfluxDb", required=True)
parser.add_argument("--influxdborg",help="The InfluxDB organization", required=True)
parser.add_argument("--influxdbbucket",help="The InfluxDB bucket", required=True)
parser.add_argument("--redishost", help="Hostname of the Redis Server", required=True)
parser.add_argument("--redispassword", help="The password for the default redis user", required=True)
parser.add_argument("-t", help="Test JSON parsing and writing",action="store_const", const=True, default=False)
parser.add_argument("-d", help="Enable debug logging of received mqtt messages", action="store_const", const=True, default=False)
args = parser.parse_args()

def saveDataToRedis(invId: str, host: str, password: str, data: dict):
    try:

        r = redis.Redis(host=host, port=6379, username="default", password=password,decode_responses=True)
        for name, value in data.items():
            r.set(f"{name}_{invId}", value)
    except:
        logger.error("Error saving data to redis.")

def savePVDataToInfluxDb(data: dict, hosturl: str, bucket: str, org: str, token: str, ts: datetime):
    try:
        with InfluxDBClient(url=hosturl, token=token, org=org) as _client:
            with _client.write_api() as _write_client:

                _write_client.write(bucket, org, Point("ac_measurements")
                    .field("watts", round(data["values"]["Pac"] * 1000))
                    .field("frequency", round(data["values"]["Fac"],2))
                    .field("simaster_watts", round(data["values"]["InvPwrAt"] * 1000))
                    .field("simaster_amps", round(data["values"]["InvCur"],2))
                    .field("simaster_voltage", round(data["values"]["InvVtg"],3))
                    .field("sislave1_watts", round(data["values"]["InvPwrAtSlv1"] * 1000))
                    .field("sislave1_amps", round(data["values"]["InvCurSlv1"],2))
                    .field("sislave1_voltage", round(data["values"]["InvVtgSlv1"],3))
                    .time(ts)
                    )
                
                _write_client.write(bucket, org, Point("battery_measurements")
                    .field("voltage", round(data["values"]["BatVtg"],3))
                    .field("soc", round(data["values"]["BatSoc"],2))
                    .field("temp", round(data["values"]["BatTmp"],2))
                    .field("total_current", round(data["values"]["TotBatCur"],3))
                    .time(ts)
                    )
    except:
        logger.error("Error saving data to influxdb.")

def write_data(data):

    saveDataToRedis("sunnyisland_master", args.redishost, args.redispassword, {
        "status": data["values"]["OpStt"]
    })
    saveDataToRedis("sunnyisland_slave1", args.redishost, args.redispassword, {
        "status": data["values"]["OpSttSlv1"]
    })
    ts = datetime.fromtimestamp(data["time"])
    savePVDataToInfluxDb(data, args.influxdbhost, args.influxdbbucket, args.influxdborg, args.influxdbtoken, ts)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    logger.info("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(args.mqtttopic)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    write_data(data)

    logger.debug(msg.topic+" "+str(msg.payload))
    
def main():
    try:

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        client.connect(args.mqtthost, args.mqttport, 60)

        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        # Other loop*() functions are available that give a threaded interface and a
        # manual interface.
        client.loop_forever()

    except:
        logger.error("Unexpected error")
        return -1
    return 0

if __name__ == "__main__":
    main()