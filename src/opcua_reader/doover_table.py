import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pydoover.docker import DeviceAgentInterface


def day_name_days_ago(tz: str, days_ago: int) -> str:
    # Get current datetime in given timezone
    now = datetime.now(ZoneInfo(tz))
    # Subtract days
    target_date = now - timedelta(days=days_ago)
    # Return day name (e.g. "Monday")
    return target_date.strftime("%A")

class DooverDataTableObject:
    def __init__(self, 
            name: str, 
            display_name: str, 
            table_description: str, 
            default_dataset: int, 
            header_display_names: dict, 
            header_order: list, 
            data: list,
            max_pages: int = 3,
            timezone: str = "UTC"
        ):
        
        self.name = name
        self.display_name = display_name
        self.table_description = table_description
        self.default_dataset = default_dataset
        self.header_display_names = header_display_names
        self.header_order = header_order
        self.max_pages = max_pages
        self.timezone = timezone
        self.data = data
        
        if len(self.data) == 0:
            self.add_page()
        
    @classmethod
    def from_dict(cls, data_dict: dict):
        """Create a DooverDataTableObject from a dictionary."""
        return cls(
            name=data_dict.get("name"),
            display_name=data_dict.get("display_name"),
            table_description=data_dict.get("table_description"),
            default_dataset=data_dict.get("default_dataset"),
            header_display_names=data_dict.get("header_display_names", {}),
            header_order=data_dict.get("header_order", []),
            data=data_dict.get("data", [])
        )
    
    def to_dict(self):
        return {
            "name": self.name,
            "display_name": self.display_name,
            "table_description": self.table_description,
            "default_dataset": self.default_dataset,
            "header_display_names": self.header_display_names,
            "header_order": self.header_order,
            "data": self.data
        }
        
    def add_entry(self, data: dict):
        self.data[-1]["data"].append(data)
        
    def add_page(self, page_name: str = None):
        if self.table_description == "Days":
            self.data.append({"data": [], "display_name": "Today"})
            while len(self.data) >= self.max_pages:
                self.data.pop(0)
                
            if self.no_of_pages > 1:
                for i in range(-2, -self.no_of_pages-1, -1):
                    match i:
                        case -2:
                            self.data[i]["display_name"] = "Yesterday"
                        case _:
                            days_ago = abs(i)+1
                            self.data[i]["display_name"] = f"{day_name_days_ago(self.timezone, days_ago)}"
        else:
            self.data.append({"data": [], "display_name": page_name})
        
    def get_page_names(self):
        return [page["page_name"] for page in self.data]
    
    @property
    def no_of_pages(self):
        return len(self.data)

class DooverTableManager:
    def __init__(self, dda: DeviceAgentInterface, channel_name: str = "doover_tables"):
        self.dda = dda
        self.channel_name = channel_name
        self._tables = {}

    async def setup(self):
        await self.pull_channel_data()
        
    async def pull_channel_data(self):
        aggregate = await self.dda.fetch_channel_aggregate(self.channel_name)
        channel_agg = aggregate.data if aggregate is not None else None

        if channel_agg is None or channel_agg == {}:
            return
        
        for table_name, table_data in channel_agg.items():
            self.add_table_from_dict(table_name, table_data)
        
    def add_table_from_dict(self, name: str, table_dict: dict):
        self.add_table(
            name=name,
            display_name=table_dict.get("display_name"),
            table_description=table_dict.get("table_description"),
            default_dataset=table_dict.get("default_dataset"),
            header_display_names=table_dict.get("header_display_names", {}),
            header_order=table_dict.get("header_order", []),
            data=table_dict.get("data", [])
        )
        
    def add_table(self, 
        name: str, 
        display_name: str, 
        table_description: str = "Days", 
        default_dataset: int = -1, 
        header_display_names: dict = {}, 
        header_order: list = [], 
        data: list = []
    ):
        if self.get_table(name) is not None:
            logging.info(f"Table {name} already exists - keeping data, updating meta data")
            self._tables[name].header_display_names = header_display_names
            self._tables[name].header_order = header_order
            self._tables[name].default_dataset = default_dataset
            self._tables[name].table_description = table_description
            self._tables[name].display_name = display_name
            return
        
        self._tables[name] = DooverDataTableObject(
            name=name,
            display_name=display_name,
            table_description=table_description,
            default_dataset=default_dataset,
            header_display_names=header_display_names,
            header_order=header_order,
            data=data
        )
        
    def get_table_data(self, name: str):
        return self.table_data.get(name, None)
    
    def get_table(self, name: str):
        return self._tables.get(name, None)
    
    async def add_page(self, name: str, page_name: str = None):
        self._tables[name].add_page(page_name)
        await self.push_update_to_channel()
    
    async def add_data_entry(self, name: str, entry: dict):
        logging.info(f"Adding data entry to table {name}: {entry}")
        logging.info(self._tables)
        self._tables[name].add_entry(entry)
        await self.push_update_to_channel()
        
    async def push_update_to_channel(self):
        table_update = {}
        for name, table in self._tables.items():
            table_update[name] = table.to_dict()
        await self.dda.update_channel_aggregate(self.channel_name, table_update)
    
    