from pymodbus.client import ModbusTcpClient
from influxdb_client import InfluxDBClient, Point
from datetime import datetime
import time, pytz
import astral
from astral.sun import sunrise, sunset
import argparse
import logging
import redis
from common import *

logger = logging.getLogger("Save Sunny Boy Power Data")
def getPVData(host: str) -> dict | None:

    try:
        client = ModbusTcpClient(host)
        client.connect()

        data = {
            "gridTotalW": Formatter.FIX0(getAddrValue(client, 30775,2,SMAType.S32)),
            "gridTotalA": Formatter.FIX3(getAddrValue(client, 30795,2,SMAType.U32)),
            "gridPhaseAA": Formatter.FIX3(getAddrValue(client, 30977,2,SMAType.S32)),
            "gridPhaseBA": Formatter.FIX3(getAddrValue(client, 30979,2,SMAType.S32)),
            "gridPhaseAW": Formatter.FIX0(getAddrValue(client, 30777,2,SMAType.S32)),
            "gridPhaseBW": Formatter.FIX0(getAddrValue(client, 30779,2,SMAType.S32)),
            "gridPhaseAV": Formatter.FIX2(getAddrValue(client, 30783,2,SMAType.U32)),
            "gridPhaseBV": Formatter.FIX2(getAddrValue(client, 30785,2,SMAType.U32)),
            "mppt1V": Formatter.FIX2(getAddrValue(client, 30771,2,SMAType.S32)),
            "mppt2V": Formatter.FIX2(getAddrValue(client, 30959,2,SMAType.S32)),
            "mppt3V": Formatter.FIX2(getAddrValue(client, 30965,2,SMAType.S32)),
            "mppt1A": Formatter.FIX3(getAddrValue(client, 30769,2,SMAType.S32)),
            "mppt2A": Formatter.FIX3(getAddrValue(client, 30957,2,SMAType.S32)),
            "mppt3A": Formatter.FIX3(getAddrValue(client, 30963,2,SMAType.S32)),
            "dailyTotalWh": Formatter.FIX0(getAddrValue(client, 30517,4,SMAType.U64)),
            "health": Formatter.TAGLIST(getAddrValue(client, 30201,2,SMAType.U32), TagList.OperationHealth),
            "status": Formatter.TAGLIST(getAddrValue(client, 40029,2,SMAType.U32), TagList.OperationStatus)
        }
        client.close()
        return data
    except:
        logger.error("Error trying to retrieve data from Sunny Boy")
        return None

def saveDataToRedis(invId: str, host: str, password: str, data: dict):
    r = redis.Redis(host=host, port=6379, username="default", password=password,decode_responses=True)
    for name, value in data.items():
        r.set(f"{name}_{invId}", value)


def savePVDataToInfluxDb(invId: str, data: dict, hosturl: str, bucket: str, org: str, token: str, ts: datetime):
    with InfluxDBClient(url=hosturl, token=token, org=org) as _client:
        with _client.write_api() as _write_client:

            _write_client.write(bucket, org, Point("pv_ac_measurements")
                                .tag("inv_id", invId)
                                .field("grid_total_watts", data["gridTotalW"])
                                .field("grid_total_amps", data["gridTotalA"])
                                .field("grid_phasea_amps", data["gridPhaseAA"])
                                .field("grid_phaseb_amps", data["gridPhaseBA"])
                                .field("grid_phasea_volts", data["gridPhaseAV"])
                                .field("grid_phaseb_volts", data["gridPhaseBV"])
                                .field("grid_phasea_watts", data["gridPhaseAW"])
                                .field("grid_phaseb_watts", data["gridPhaseBW"])
                                .time(ts)
                                )
            
            _write_client.write(bucket, org, Point("pv_dc_measurements")
                                .tag("inv_id", invId)
                                .field("mppt1_volts", data["mppt1V"])
                                .field("mppt2_volts", data["mppt2V"])
                                .field("mppt3_volts", data["mppt3V"])
                                .field("mppt1_amps", data["mppt1A"])
                                .field("mppt2_amps", data["mppt2A"])
                                .field("mppt3_amps", data["mppt3A"])
                                .time(ts)
                                )


parser = argparse.ArgumentParser(description="SMA PV Data Collection Shell")
parser.add_argument("--sunnyboyhost",help="The hostname of the Sunny Boy", required=True)
parser.add_argument("--influxdbhost",help="The hostname of InfluxDb", required=True)
parser.add_argument("--influxdbtoken",help="The API token for InfluxDb", required=True)
parser.add_argument("--influxdborg",help="The InfluxDB organization", required=True)
parser.add_argument("--influxdbbucket",help="The InfluxDB bucket", required=True)
parser.add_argument("--redishost", help="Hostname of the Redis Server", required=True)
parser.add_argument("--invid", help="Inverter id. May be numberic or a label", required=True)
parser.add_argument("--redispassword", help="The password for the default redis user", required=True)
parser.add_argument("--repeat", type=int, help="Frequency of operation, in seconds.", default=15)
parser.add_argument("-t", action="store_const", const=True, default=False)
parser.add_argument("--lat", help="The latitude of the inverter", type=float, required=True)
parser.add_argument("--lon", help="The longitude of the inverter", type=float, required=True)
args = parser.parse_args()

def main():

    ob = astral.Observer(latitude=args.lat,longitude=args.lon, elevation=0.0) 

    while(True):
        now = pytz.UTC.localize(datetime.utcnow())
        sunset_time = sunset(ob, now)
        sunrise_time = sunrise(ob, now)

        daytime = now > sunrise_time and now < sunset_time
        # If not daytime, sleep until sunrise
        if not daytime:
            sleep_seconds = (sunrise_time - now).seconds
            logger.info(f'Nighttime. Will stop recording data for {sleep_seconds} seconds until sunrise at {sunrise_time}')
            time.sleep(sleep_seconds)

        start = time.time()
        if (args.t):
            logger.info("Running in test mode. Using dummy PV data")
            pvdata = {"gridTotalW": 141, "gridTotalA": 0.703, "gridPhaseAA": 0.703, "gridPhaseBA": 0.703, "gridPhaseAW": 70, "gridPhaseBW": 71, "gridPhaseAV": 119.94, "gridPhaseBV": 120.35, "mppt1V": 358.38, "mppt2V": 358.07, "mppt3V": 358.23, "mppt1A": 0.247, "mppt2A": 0.176, "mppt3A": 0.038, "dailyTotalWh": 2294,"health": "Ok", "status": "Derating"}
        else:
            pvdata = getPVData(args.sunnyboyhost)

        if pvdata == None:

            saveDataToRedis(args.invid, args.redishost, args.redispassword, {
                "health": "Unreachable"
            })
            # Try again in 10 minutes
            logger.warning(f'Sunny Boy at {args.sunnyboyhost} is not reachable. Will try again in 10 minutes')
            time.sleep(600)
        else:
            saveDataToRedis(args.invid, args.redishost, args.redispassword, {
                "pv_total": pvdata["dailyTotalWh"],
                "health": pvdata["health"],
                "status": pvdata["status"]
                })
            
            savePVDataToInfluxDb(args.invid, pvdata, args.influxdbhost, args.influxdbbucket, args.influxdborg, args.influxdbtoken, now)

        runtime = round(time.time() - start)
        if (runtime < args.repeat):
            time.sleep(args.repeat - runtime)
    
if __name__ == "__main__":
    main()

# token = "ovMm-o8jjzQpAjRsDUNrm5ZK_XexNqiguld37aYfte2IYKtOM8VID9MUOsipJTSuKp_IrnHLSLNjnorlqau0Tg=="

"""
Sample command-line, using -t test flag.
$ python save-sunny-boy-power-data.py --sunnyboyhost sma3013980643 --invid sunnyboy1 --redishost localhost --redispassword nimda1234 --influxdbhost http://localhost:8086 --influxdbtoken 3Nj5jtGSROxcuJg_r-4CJKVIqql_5NLSYjPEuMCzNKpdTqKAna57JdkW0c_UldrEvRepVvWKM0J_Mx567972vQ== --influxdborg pv_data --influxdbbucket pv_data --lat 36.17 --lon -82.86 -t
"""
