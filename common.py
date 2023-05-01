from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from enum import Enum

class SMAType(Enum):
    S16 = 1
    S32 = 2
    STR32 = 3
    U16 = 4
    U32 = 5
    U64 = 6
            
def decodeRegisters(registers, type: SMAType):
        msg = BinaryPayloadDecoder.fromRegisters(registers, byteorder = Endian.Big)
        
        match type:
            case SMAType.U16:
                return msg.decode_16bit_uint()
            case SMAType.U32:
                return msg.decode_32bit_uint()
            case SMAType.U64:
                return msg.decode_64bit_uint()
            case SMAType.S16:
                return msg.decode_16bit_int()
            case SMAType.S32:
                return msg.decode_32bit_int()
            case SMAType.STR32:
                return msg.decode_string(32)

class TAGLIST():
    
    def __init__(self, name: str, tags = {}):
        self.tags = tags
        self.name = name

    def toTag(self, value: int):
        if value not in self.tags:
            msg = f'Value {value} not found in taglist {self.name}'
            raise RuntimeError(msg)
        return self.tags[value]

class TagList:
    OperationHealth = TAGLIST("OperationHealth", {
        35: "Fault",
        303: "Off",
        307: "Ok",
        455: "Warning",
        937: "_" #Listed on page 58 of WEBBOX_SC-COM-MODBUS-TD-en-16.pdf
    })

    """Operation.OpStt"""
    OperationStatus = TAGLIST("OperationStatus", {
        295: "MPP",
        381: "Stop",
        443: "Constant voltage",
        1392: "Fault",
        1393: "Waiting for PV voltage",
        1467: "Start",
        1469: "Shut down",
        1480: "Waiting for utilities company",
        1855: "Stand-alone operation",
        2119: "Derating",
        16777213: "Information not available"
    })
    

class Formatter:

    """
    Formatters for various SMA data format. Data returned in the modbus registers will
    typically be U32 (32-bit word) or S32 (signed 32-bit word). Some values stored in
    these registers represent fractional data, such as 0.587A, or 360.78V. These values
    are stored and returned as plain integer values, so they must be formatted.

    Refer to the SMA modbus documentation to determine the data formatter to use.

    """

    """
    Does not change the value.
    """
    def FIX0(value: int) -> int:
        return value

    """
    Formats integer to one decimal float.
    """
    def FIX1(value: int) -> float:
        return value/10

    """
    Formats integer to two decimal float.
    """
    def FIX2(value: int) -> float:
        return value/100

    """
    Formats integer to three decimal float.
    """
    def FIX3(value: int) -> float:
        return value/1000
    
    """
    Formats integer to four decimal float.
    """
    def FIX4(value: int) -> float:
        return value/10000
    
    """
    Formats the integer value into a human readable label associated
    with a particular register. Calling code must specify the
    TAGLIST to use when formatting. If the actual register value
    is not included in the specified TAGLIST, and error is raised.
    """
    def TAGLIST(value: int, taglist: TAGLIST) -> str:
        return taglist.toTag(value)
    



def getAddrValue(client: ModbusTcpClient, address: int, count: int, type: SMAType):
    result = client.read_holding_registers(address, count, 3)
    if (result.__class__ == "ExceptionResponse"):
        raise RuntimeError(result)
    registers: list = result.registers
    return decodeRegisters(registers, type)