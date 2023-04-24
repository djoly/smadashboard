from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from enum import Enum
from influxdb_client import InfluxDBClient, Point, WriteOptions
from datetime import datetime
import argparse

from common import *


def getStatusData(host: str):

    client = ModbusTcpClient(host, port)
    client.connect()

    data = {
        "health": Formatter.TAGLIST(getAddrValue(client, 30201,2,SMAType.U32), TagList.OperationHealth),
        "status": Formatter.TAGLIST(getAddrValue(client, 40029,2,SMAType.U32), TagList.OperationStatus)
    }
    return data