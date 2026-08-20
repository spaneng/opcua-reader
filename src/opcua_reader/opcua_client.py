import asyncio
import logging
from typing import Callable

from asyncua import Client, ua
from asyncua.common.subscription import Subscription

log = logging.getLogger()
class AsyncUAClient:
    def __init__(self, url: str):
        self.url = url
        self.client = Client(url)
        self.nodes = {}
        self.subscriptions = []
        self.sub_handler_map = []
        
    async def setup(self):
        await self.connect()
        
        log.info("Client setup complete")

    async def connect(self):
        await self.client.connect()
        log.info(f"Connected to {self.url}")

    async def disconnect(self):
        for sub, handle in self.sub_handler_map:
            await sub.unsubscribe(handle)
        for sub in self.subscriptions:
            await sub.delete()
        await self.client.disconnect()
        log.info("Disconnected")

    async def add_subscription(self, nodeid_str: str, callback, cb_period: int = 500):
        """
        nodeid_str: e.g. "ns=2;s=LevelTank1"
        callback: async or sync function to call on data change
        """
        node = self.client.get_node(nodeid_str)

        class SubHandler:
            def datachange_notification(self, node, val, data):
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(node, val))
                else:
                    callback(node, val)

        handler = SubHandler()
        subscription: Subscription = await self.client.create_subscription(cb_period, handler)
        try:
            handle = await subscription.subscribe_data_change(node)
        except Exception as e:
            log.error(f"Error subscribing to {nodeid_str}: {e}")
            return

        self.subscriptions.append(subscription)
        self.sub_handler_map.append((subscription, handle))
        log.info(f"Subscribed to {nodeid_str}")
    
    async def create_shared_subscription(
        self, 
        node_callbacks: dict[str, Callable],
        publishing_interval: int = 1000,
        lifetime_count: int = 20000,
        max_keep_alive_count: int = 10000
    ) -> Subscription:
        """
        Create a single shared subscription for multiple nodes with optimized parameters.
        This helps prevent "Subscription state changed (Late)" errors by reducing
        the number of subscriptions and properly configuring timing parameters.
        
        :param node_callbacks: Dictionary mapping node_id strings to their callback functions
        :param publishing_interval: Publishing interval in milliseconds (default 1000ms)
        :param lifetime_count: Requested lifetime count (default 20000)
        :param max_keep_alive_count: Requested max keep-alive count (default 10000)
        :return: The created Subscription object
        """
        # Store node objects for comparison
        node_objects = {nodeid_str: self.client.get_node(nodeid_str) for nodeid_str in node_callbacks}
        
        # Create a handler that routes notifications to the appropriate callback
        class SharedSubHandler:
            def __init__(self, callbacks: dict, node_objs: dict):
                self.callbacks = callbacks
                self.node_objects = node_objs
            
            def datachange_notification(self, node, val, data):
                # Find the matching node_id_str by comparing nodeid objects
                node_id_str = None
                for key, node_obj in self.node_objects.items():
                    if node_obj.nodeid == node.nodeid:
                        node_id_str = key
                        break
                
                if node_id_str is None:
                    # Fallback: try string comparison
                    node_id_str = str(node.nodeid)
                
                callback = self.callbacks.get(node_id_str)
                
                if callback:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(node, val))
                    else:
                        callback(node, val)
                else:
                    log.warning(f"No callback found for node {node_id_str}")
        
        handler = SharedSubHandler(node_callbacks, node_objects)
        
        # Create subscription with optimized parameters
        params = ua.CreateSubscriptionParameters()
        params.RequestedPublishingInterval = publishing_interval
        params.RequestedLifetimeCount = lifetime_count
        params.RequestedMaxKeepAliveCount = max_keep_alive_count
        params.MaxNotificationsPerPublish = 10000
        params.PublishingEnabled = True
        params.Priority = 0
        
        subscription: Subscription = await self.client.create_subscription(params, handler)
        
        # Subscribe to all nodes in the shared subscription
        for nodeid_str, callback in node_callbacks.items():
            try:
                node = node_objects[nodeid_str]
                handle = await subscription.subscribe_data_change(node)
                self.sub_handler_map.append((subscription, handle))
                log.info(f"Added {nodeid_str} to shared subscription")
            except Exception as e:
                log.error(f"Error subscribing to {nodeid_str} in shared subscription: {e}")
        
        self.subscriptions.append(subscription)
        log.info(f"Created shared subscription with {len(node_callbacks)} monitored items")
        return subscription
        
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
                log.debug(f"Node {nodeid_str} already registered.")
                continue
            try:
                node = self.client.get_node(nodeid_str)
            except Exception as e:
                log.error(f"Error getting node {nodeid_str}: {e}")
                continue
            self.nodes[nodeid_str] = node
            log.debug(f"Registered node: {nodeid_str}")
            
    async def read_value(self, nodeid_str: str):
        """
        Read the value of a node by its NodeId string.
        """
        if nodeid_str not in self.nodes:
            logging.error(f"Node {nodeid_str} not registered.")
            self.nodes[nodeid_str] = self.client.get_node(nodeid_str)
        node = self.nodes[nodeid_str]
        try:
            value = await node.read_value()
            return value
        except Exception as e:
            log.warning(f"Error reading value from {nodeid_str}: {e}")
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
