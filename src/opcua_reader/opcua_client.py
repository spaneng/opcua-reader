import asyncio
from asyncua import Client, ua
from asyncua.common.subscription import Subscription

class AsyncUAClient:
    def __init__(self, url: str):
        self.url = url
        self.client = Client(url)
        self.nodes = {}
        self.subscriptions = []
        self.sub_handler_map = []
        
    async def setup(self):
        await self.connect()
        
        print("Client setup complete")

    async def connect(self):
        await self.client.connect()
        print(f"Connected to {self.url}")

    async def disconnect(self):
        for sub, handle in self.sub_handler_map:
            await sub.unsubscribe(handle)
        for sub in self.subscriptions:
            await sub.delete()
        await self.client.disconnect()
        print("Disconnected")

    async def add_subscription(self, nodeid_str: str, callback, cb_period: int = 500):
        """
        nodeid_str: e.g. "ns=2;s=LevelTank1"
        callback: async or sync function to call on data change
        """
        node = self.client.get_node(nodeid_str)

        class SubHandler:
            def datachange_notification(inner_self, node, val, data):
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(node, val))
                else:
                    callback(node, val)

        handler = SubHandler()
        subscription: Subscription = await self.client.create_subscription(cb_period, handler)
        handle = await subscription.subscribe_data_change(node)

        self.subscriptions.append(subscription)
        self.sub_handler_map.append((subscription, handle))
        print(f"Subscribed to {nodeid_str}")
        
    async def get_node_id_val(self, nodeid_str: str):
        """
        Get the value of a node by its NodeId string.
        """
        node = self.client.get_node(nodeid_str)
        return await node.read_value()
    
    async def register_nodes(self, node_ids: list[str]):
        """
        Register multiple nodes by their NodeId strings.
        """
        for nodeid_str in node_ids:
            node = self.nodes.get(nodeid_str, None)
            if node is not None:
                print(f"Node {nodeid_str} already registered.")
                continue
            try:
                node = self.client.get_node(nodeid_str)
            except Exception as e:
                print(f"Error getting node {nodeid_str}: {e}")
                continue
            self.nodes[nodeid_str] = node
            print(f"Registered node: {nodeid_str}")
            
    async def read_value(self, nodeid_str: str):
        """
        Read the value of a node by its NodeId string.
        """
        if nodeid_str not in self.nodes:
            print(f"Node {nodeid_str} not registered.")
            self.nodes[nodeid_str] = self.client.get_node(nodeid_str)
        node = self.nodes[nodeid_str]
        try:
            value = await node.read_value()
            return value
        except Exception as e:
            print(f"Error reading value from {nodeid_str}: {e}")
            return None

async def main():
    
    async def my_callback(node, val):
        print(f"Value from {await node.read_display_name()}: {val} mMol/L")
        
    def my_sync_callback(node, val):
        print(f"Sync callback - Value from {node}: {val} degrees C")
        
    client = AsyncUAClient("opc.tcp://localhost:4840")
    await client.setup()
    
    await client.add_subscription("ns=2;i=3", my_callback)

    try:
        while True:
            await asyncio.sleep(10)
            await client.add_subscription("ns=2;i=2", my_sync_callback)
            
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
