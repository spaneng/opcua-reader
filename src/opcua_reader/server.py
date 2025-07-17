import asyncio
import random
import json
import logging
from asyncua import Server, ua
from pathlib import Path



class SimulatedOPCUAServer:
    def __init__(self, endpoint="opc.tcp://0.0.0.0:4840/"):
        self.endpoint = endpoint
        self.server = Server()
        self.namespace_uri = "test"
        self.variables = {}
        self.a_variables = {}
        
        self.warning_vars =["Active", "AlarmText", "Code", "Timestamp", "Severity"]
        
        json_path = Path(__file__).parent / "server_context.json"
        print("Loading server context from:", json_path)
        with open(json_path, "r") as f:
            config = json.load(f)
            
        self.server_context = config.get("server_context", {})
        print("Server context:", self.server_context)

    async def setup(self):
        await self.server.init()
        self.server.set_endpoint(self.endpoint)

        test_idx = await self.server.register_namespace("test1")
        ns_idx = await self.server.register_namespace(self.namespace_uri)
        analog_obj = await self.server.nodes.objects.add_object(ns_idx, "DB_OPCUA_AnalogValues")
        report_obj = await self.server.nodes.objects.add_object(ns_idx, "DB_OPCUA_Report")
        warnings_obj = await self.server.nodes.objects.add_object(ns_idx, "DB_OPCUA_Warnings")

        # Analog variables
        analog_nodes = self.server_context.get("analog_nodes", {})

        for name, val in analog_nodes.items():
            node = await analog_obj.add_variable(
                ua.NodeId(f'"DB_OPCUA_AnalogValues"."{name}"', ns_idx),
                name,
                val
            )
            await node.set_writable()
            self.a_variables[node] = val

        # Report variables
        report_nodes = self.server_context.get("report_nodes", {})

        for name, val in report_nodes.items():
            node = await report_obj.add_variable(
                ua.NodeId(f'"DB_OPCUA_Report"."{name}"', ns_idx),
                name,
                val
            )
            if name == "BatchStartTime1":
                self.batch_test_node = node
            await node.set_writable()
            self.variables[node] = val
            
        # Warnings variables
        warnings_ids = self.server_context.get("warning_nodes", [])
        print(" \n\n\n Warnings IDs:", warnings_ids, "\n\n\n")
        for name in warnings_ids:
            
            var = "Active"
            full_name = f"{name}_{var}"
            node = await warnings_obj.add_variable(
                ua.NodeId(f'"DB_OPCUA_Warnings"."Warnings"[{name}]."{var}"', ns_idx),
                full_name,
                False  # Default value for warnings
            )
            await node.set_writable()
            self.variables[node] = False
            self.test_alarm_node = node
            
            var = "AlarmText"
            full_name = f"{name}_{var}"
            node = await warnings_obj.add_variable(
                ua.NodeId(f'"DB_OPCUA_Warnings"."Warnings"[{name}]."{var}"', ns_idx),
                full_name,
                f'{full_name} Alarm Text!'  # Default value for warnings
            )
            await node.set_writable()
            self.variables[node] = f'{full_name} Alarm Text!'
            
            var = "Code"
            full_name = f"{name}_{var}"
            node = await warnings_obj.add_variable(
                ua.NodeId(f'"DB_OPCUA_Warnings"."Warnings"[{name}]."{var}"', ns_idx),
                full_name,
                f"{name}_{var} [CODE]"  # Default value for warnings
            )
            await node.set_writable()
            self.variables[node] = f"{name}_{var} [CODE]" 
            
            var = "Severity"
            full_name = f"{name}_{var}"
            node = await warnings_obj.add_variable(
                ua.NodeId(f'"DB_OPCUA_Warnings"."Warnings"[{name}]."{var}"', ns_idx),
                full_name,
                f"{name}_{var} [SEVERITY]"  # Default value for warnings
            )
            await node.set_writable()
            self.variables[node] = f"{name}_{var} [SEVERITY]"
            
            var = "Timestamp"
            full_name = f"{name}_{var}"
            node = await warnings_obj.add_variable(
                ua.NodeId(f'"DB_OPCUA_Warnings"."Warnings"[{name}]."{var}"', ns_idx),
                full_name,
                f"{name}_{var} [TIMESTAMP]"  # Default value for warnings
            )
            await node.set_writable()
            self.variables[node] = f"{name}_{var} [TIMESTAMP]"


    async def start(self):
        async with self.server:
            print(f"OPC UA Server running at {self.endpoint}")
            task_1 = asyncio.create_task(self._update_values())
            task_2 = asyncio.create_task(self.test_alarm())
            task_3 = asyncio.create_task(self.test_report())
            await asyncio.gather(task_1, task_2, task_3)
            # while True:
            #     await self._update_values()
            #     await asyncio.sleep(1)
                
    async def test_alarm(self):
        while True:
            await asyncio.sleep(30)
            print("Alarm triggered for node:", self.test_alarm_node)
            await self.test_alarm_node.write_value(True)
            await asyncio.sleep(5)
            await self.test_alarm_node.write_value(False)
            
    async def test_report(self):
        """
        Test function to simulate report updates.
        """
        node = self.batch_test_node 
        print("Testing report updates for node:", node)
        count = 0
        while True:
            print("Updating report values...")
            await asyncio.sleep(20)
            await node.write_value(f"New Time {count}")
            await asyncio.sleep(2)
            
            count+= 1

    async def _update_values(self):
        
        while True:
            print("Updating analogue values...")
            for node, base_val in self.a_variables.items():
                if isinstance(base_val, bool):
                    # Toggle randomly (10% chance)
                    if random.random() < 0.1:
                        new_val = not await node.read_value()
                        # print("new value for", node, "is", new_val)
                        await node.write_value(new_val)
                elif isinstance(base_val, (int, float)):
                    percent_change = 1 + random.uniform(-0.05, 0.05)
                    new_val = round(base_val * percent_change, 2)
                    # print("new value for", node, "is", new_val)
                    await node.write_value(new_val)
                    
            print("Updating report number values...")
            for node, base_val in self.variables.items():
                if not isinstance(base_val, bool):
                    if isinstance(base_val, (int, float)):
                        percent_change = 1 + random.uniform(-0.05, 0.05)
                        new_val = round(base_val * percent_change, 2)
                        # print("new value for", node, "is", new_val)
                        await node.write_value(new_val)
            await asyncio.sleep(2)

async def main():
    server = SimulatedOPCUAServer()
    await server.setup()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
