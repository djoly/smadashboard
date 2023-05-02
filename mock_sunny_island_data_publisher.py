import paho.mqtt.client as mqtt
import datetime,time, pytz, json, argparse, logging

logger = logging.getLogger("Mock Save Sunny Island Data Publisher Script")

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
    
    while(True):
        try:
            testJsonData["time"] = round(time.time())
            client.connect(args.mqtthost, args.mqttport, 60)
            client.publish(args.mqtttopic, json.dumps(testJsonData))
            client.disconnect()
            time.sleep(15)
        except:
            logging.error("Error publishing mock data")
            return -1


if __name__ == "__main__":
    main()
