import asyncio
from asyncua import Server
import random

async def main():
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")
    server.set_server_name("Temperature OPC UA Server")

    # Register a namespace
    uri = "http://example.org/temperature"
    idx = await server.register_namespace(uri)

    # Create a new object with a variable
    
    objects = server.nodes.objects
    temp_obj = await objects.add_object(idx, "TemperatureSensor")
    temp_var = await temp_obj.add_variable(idx, "Temperature", 25.0)
    o2_var = await temp_obj.add_variable(idx, "OxygenLevel", 21.0)
    await temp_var.set_writable()

    async with server:
        print("OPC UA Server running at opc.tcp://localhost:4840/freeopcua/server/")
        while True:
            # Simulate temperature change
            new_temp = 20 + random.random() * 10
            new_02 = 20 + random.random() * 5
            await temp_var.write_value(new_temp)
            await o2_var.write_value(new_02)
            await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())