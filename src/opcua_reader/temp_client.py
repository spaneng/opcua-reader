import asyncio
from asyncua import Client, ua

async def main():
    url = "opc.tcp://192.168.1.190:8030"
    async with Client(url=url) as client:
        print("Connected to OPC UA Server")

        # Browse for the temperature variable
        root = client.nodes.root
        objects = client.nodes.objects

        print("Root node is:", root)
        print("Objects node is:", objects)
        print("client.nodes = ", client.nodes.__dict__)
        

        # nsidx = await client.get_namespace_index("http://example.org/temperature")
        # print("Namespace index for 'http://example.org/temperature' is:", nsidx)

        # Get the TemperatureSensor object
        # temp_sensor = await objects.get_child([f"{nsidx}:TemperatureSensor"])
        # temp_var = await temp_sensor.get_child([f"{nsidx}:Temperature"])
        
        device_set = await objects.get_child(["2:DeviceSet"])
        test_zamil = await device_set.get_child(["3:Test Zamil"])
        datablocks = await test_zamil.get_child(["3:DataBlocksGlobal"])
        inputs = await datablocks.get_child(["3:DB_OPCUA_AnalogValues"])
        level_tank_1 = await inputs.get_child(["3:LevelTank1"])
        level_tank_2 = await inputs.get_child(["3:LevelTank2"])
        # temp_pump_1 = await inputs.get_child(["3:TEMPERATURE PUMP 1"])
        # temp_pump_2 = await inputs.get_child(["3:TEMPERATURE PUMP 2"])
        # pump_1_run = await inputs.get_child(["3:Injection Pump 1 Run"])
        
        print("device_set node is:", device_set)
        print("test_zamil node is:", test_zamil)
        print("inputs node is:", inputs)
        print("level_tank node is:", level_tank_1)
        print("level_tank node is:", level_tank_2)
        # print("temp_pump_1 node is:", temp_pump_1)
        # print("temp_pump_2 node is:", temp_pump_2)
        
        # temp_sensor = await objects.get_child(["2:TemperatureSensor"])
        # temp_sensor = await objects.get_child(["3:TemperatureSensor"])
        
        # print("TemperatureSensor node is:", temp_sensor)
        # # print("TemperatureSensor node is:", temp_sensor.__dict__)
        # test_zamil = await temp_sensor.get_child(["2:Test Zamil"])
        # inputs = await 
        
        # o2_var = await temp_sensor.get_child(["2:OxygenLevel"])

        # test1 = await objects.get_child(["2:OxygenLevel"])

        # nodeid = ua.NodeId(3, nsidx)
        # test_node = client.get_node(nodeid)
        

        while True:
            val = await level_tank_1.read_value()
            print(f"level tank is: {val:.2f} %")
            val = await level_tank_2.read_value()
            print(f"level tank 2 is: {val:.2f} %")
            # val = await temp_pump_1.read_value()
            # print(f"temp_pump_1 is: {val:.2f} %")
            # val = await temp_pump_2.read_value()
            # print(f"temp_pump_2 is: {val:.2f} %")
            # val = await pump_1_run.read_value()
            # print(f"pump_1 running is: {val}")
            
            # o2_val = await o2_var.read_value()
            # print(f"Oxygen Level: {o2_val:.2f} %")
            # test_val = await test_node.read_value()
            # print(f"Test Value: {test_val}")

            # test_val_1 = await test1.read_value()
            # print(f"Test1 Value: {test_val_1}")

            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())