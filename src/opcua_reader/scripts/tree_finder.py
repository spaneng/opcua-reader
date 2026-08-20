import asyncio

from asyncua import Client, ua


async def print_tree(node, indent="", last=True, visited=None):
    """
    Recursive pretty tree printer for OPC UA nodes.
    """
    if visited is None:
        visited = set()

    # Avoid infinite loops
    if node.nodeid in visited:
        print(indent + ("└─ " if last else "├─ ") + f"{await node.read_display_name()}  (↺ revisited)")
        return
    visited.add(node.nodeid)

    # Node name
    display_name = (await node.read_display_name()).Text
    print(indent + ("└─ " if last else "├─ ") + display_name)

    # Update indentation for children
    indent += "   " if last else "│  "

    # Get hierarchical children
    children = await node.get_children()

    # Recursively print children
    for i, child in enumerate(children):
        is_last = (i == len(children) - 1)
        await print_tree(child, indent, is_last, visited)


async def main():
    url = "opc.tcp://192.168.102.10:4840"  # change to your OPC UA server URL
    async with Client(url) as client:
        root = client.get_root_node()
        print("Root")
        await print_tree(root, "", True)

if __name__ == "__main__":
    asyncio.run(main())
