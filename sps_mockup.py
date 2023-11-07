#!/usr/bin/env python3
"""
Pymodbus Synchronous Server Example
--------------------------------------------------------------------------

The synchronous server is implemented in pure python without any third
party libraries (unless you need to use the serial protocols which require
pyserial). This is helpful in constrained or old environments where using
twisted is just not feasible. What follows is an example of its use:
"""
# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
from pymodbus.version import version
from pymodbus.server.sync import StartTcpServer
from pymodbus.server.sync import StartTlsServer
from pymodbus.server.sync import StartUdpServer
from pymodbus.server.sync import StartSerialServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer

from threading import Thread
import time
# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
# import logging
# FORMAT = ('%(asctime)-15s %(threadName)-15s'
#           ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
# logging.basicConfig(format=FORMAT)
# log = logging.getLogger()
# log.setLevel(logging.DEBUG)


def sps_simulation(context):
    time.sleep(5)
    fb_values = {
        "V1":1,
        "V2":0,
        "V3":0,
        "V4":0,
        "PUMP":1,
        "UPPER_MAGNETIC_VALVE":0,
        "LOWER_MAGNETIC_VALVE":0,
        "HEAT_A":0,
        "HEAT_B":0,
        "COOL_A":0,
        "COOL_B":0,
        "TIDE_A":100,
        "TIDE_B":100,
        "TEMP_SETPOINT_A":1200,
        "TEMP_SETPOINT_B":1200,
        "SPARE_16":0,
        "SPARE_17":0,
        "SPARE_18":0,
        "LAST_STEP_NUMBER":2,
        "MANUAL_CONTROL":0,
        "RO_TEMP":1250,
        "RO_PH":1360,
        "RO_COND":1470,
        "RO_OXYGEN":1580,
        "RO_SPARE_25":0,
        "RO_SPARE_26":0,
        "RO_SPARE_27":0,
        "RO_SPARE_28":0,
        "RO_SPARE_29":0,
        "RO_SPARE_30":0,
        "RO_SPARE_31":0,
        "RO_SPARE_32":0
    }

    wr_values = {
        "V1":1,
        "V2":0,
        "V3":0,
        "V4":0,
        "PUMP":1,
        "UPPER_MAGNETIC_VALVE":0,
        "LOWER_MAGNETIC_VALVE":0,
        "HEAT_A":0,
        "HEAT_B":0,
        "COOL_A":0,
        "COOL_B":0,
        "TIDE_A":100,
        "TIDE_B":100,
        "TEMP_SETPOINT_A":1200,
        "TEMP_SETPOINT_B":1200,
        "SPARE_16":0,
        "SPARE_17":0,
        "SPARE_18":0,
        "SPARE_19":0,
        "SPARE_20":0,
        "SPARE_21":0,
        "SPARE_22":0,
        "SPARE_23":0,
        "SPARE_24":0,
        "SPARE_25":0,
        "SPARE_26":0,
        "SPARE_27":0,
        "SPARE_28":0,
        "SPARE_29":0,
        "HEARTBEAT":0,
        "LAST_STEP_NUMBER":2,
        "MANUAL_CONTROL":0
    }
    context[0].setValues(3, 32001, list(wr_values.values()))
    context[0].setValues(3, 32033, list(fb_values.values()))

    timeout = 2

    while(True):
        # copy written values to feedback registers
        written = context[0].getValues(3, 32001, 32)
        for idx, key in enumerate(wr_values):
            wr_values[key] = written[idx]
        
        for key in wr_values:
            if key in fb_values.keys():
                fb_values[key] = wr_values[key]

        holding = list(fb_values.values())
        context[0].setValues(3, 32033, holding)

        string = ""
        for i in range(32):
            string += f"\n{list(fb_values)[i]:>20}: {list(fb_values.values())[i]:4},\t{list(wr_values)[i]:>20}: {list(wr_values.values())[i]:4}"
        print("\nFeedback-Values:\t\tWrite-Values:" + string)

        # check Heartbeat
        heartbeat = wr_values["HEARTBEAT"]
        if heartbeat == 1:
            timeout = 0
        else:
            timeout = timeout + 1 if timeout < 2 else 2
        
        if timeout >= 2:
            print("Heartbeat: Not present")
        else:
            print("Heartbeat: OK")
        
        context[0].setValues(3, 32030, [0])

        
        time.sleep(5)
        



def run_server():
    # ----------------------------------------------------------------------- #
    # initialize your data store
    # ----------------------------------------------------------------------- #
    # The datastores only respond to the addresses that they are initialized to
    # Therefore, if you initialize a DataBlock to addresses of 0x00 to 0xFF, a
    # request to 0x100 will respond with an invalid address exception. This is
    # because many devices exhibit this kind of behavior (but not all)::
    #
    # block = ModbusSequentialDataBlock(32001, [0]*64)
    #
    # Continuing, you can choose to use a sequential or a sparse DataBlock in
    # your data context.  The difference is that the sequential has no gaps in
    # the data while the sparse can. Once again, there are devices that exhibit
    # both forms of behavior::
    #
    #     block = ModbusSparseDataBlock({0x00: 0, 0x05: 1})
    #     block = ModbusSequentialDataBlock(0x00, [0]*5)
    #
    # Alternately, you can use the factory methods to initialize the DataBlocks
    # or simply do not pass them to have them initialized to 0x00 on the full
    # address range::
    #
    #     store = ModbusSlaveContext(di = ModbusSequentialDataBlock.create())
    #     store = ModbusSlaveContext()
    #
    # Finally, you are allowed to use the same DataBlock reference for every
    # table or you may use a separate DataBlock for each table.
    # This depends if you would like functions to be able to access and modify
    # the same data or not::
    #
    #     block = ModbusSequentialDataBlock(0x00, [0]*0xff)
    #     store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
    #
    # The server then makes use of a server context that allows the server to
    # respond with different slave contexts for different unit ids. By default
    # it will return the same context for every unit id supplied (broadcast
    # mode).
    # However, this can be overloaded by setting the single flag to False and
    # then supplying a dictionary of unit id to context mapping::
    #
    #     slaves  = {
    #         0x01: ModbusSlaveContext(...),
    #         0x02: ModbusSlaveContext(...),
    #         0x03: ModbusSlaveContext(...),
    #     }
    #     context = ModbusServerContext(slaves=slaves, single=False)
    #
    # The slave context can also be initialized in zero_mode which means that a
    # request to address(0-7) will map to the address (0-7). The default is
    # False which is based on section 4.4 of the specification, so address(0-7)
    # will map to (1-8)::
    #
    #     store = ModbusSlaveContext(..., zero_mode=True)
    # ----------------------------------------------------------------------- #
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(32001, [0]*64),
        # ir=ModbusSequentialDataBlock(32001, [0]*32),
        zero_mode=True)

    context = ModbusServerContext(slaves=store, single=True)

    # ----------------------------------------------------------------------- #
    # initialize the server information
    # ----------------------------------------------------------------------- #
    # If you don't set this or any fields, they are defaulted to empty strings.
    # ----------------------------------------------------------------------- #
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'Pymodbus'
    identity.ProductCode = 'PM'
    identity.VendorUrl = 'http://github.com/riptideio/pymodbus/'
    identity.ProductName = 'Pymodbus Server'
    identity.ModelName = 'Pymodbus Server'
    identity.MajorMinorRevision = version.short()

    # ----------------------------------------------------------------------- #
    # run the server you want
    # ----------------------------------------------------------------------- #
    # Tcp:
    sim_thread = Thread(target=sps_simulation, args=(context,), daemon=True)
    sim_thread.start()
    StartTcpServer(context, identity=identity, address=("", 5020))
    #
    # TCP with different framer
    # StartTcpServer(context, identity=identity,
    #                framer=ModbusRtuFramer, address=("0.0.0.0", 5020))

    # TLS
    # StartTlsServer(context, identity=identity, certfile="server.crt",
    #                keyfile="server.key", address=("0.0.0.0", 8020))

    # Udp:
    # StartUdpServer(context, identity=identity, address=("0.0.0.0", 5020))

    # socat -d -d PTY,link=/tmp/ptyp0,raw,echo=0,ispeed=9600 PTY,link=/tmp/ttyp0,raw,echo=0,ospeed=9600
    # Ascii:
    # StartSerialServer(context, identity=identity,
    #                    port='/dev/ttyp0', timeout=1)

    # RTU:
    # StartSerialServer(context, framer=ModbusRtuFramer, identity=identity,
    #                   port='/tmp/ttyp0', timeout=.005, baudrate=9600)

    # Binary
    # StartSerialServer(context,
    #                   identity=identity,
    #                   framer=ModbusBinaryFramer,
    #                   port='/dev/ttyp0',
    #                   timeout=1)


if __name__ == "__main__":
    try:
        run_server()
    except KeyboardInterrupt:
        print("Exiting...")
