import os
import sys

from build_pdf import build_pdf

## Add the include directory to the path if it is not already there.
include_dir = os.path.join(os.path.dirname(__file__), 'include')
if not include_dir in sys.path:
    sys.path.append(include_dir)
    
from pydoover.reports.base import ReportGenerator
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def find_reconciliation(obj, target_key="Reconciliation"):
        """
        Recursively search for the sub-object with the given key
        inside a nested dictionary structure.
        """
        if not isinstance(obj, dict):
            return None

        for key, value in obj.items():
            if key == target_key:
                return value  # found it!
            if isinstance(value, dict):
                result = find_reconciliation(value, target_key)
                if result is not None:
                    return result
        return None

class InjectorReportGenerator(ReportGenerator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def retrieve_report_data(self):
        series, msgs = super().retrieve_report_data()
        
    def get_file_outputs(self) -> list:
        """
        Returns a list of expected output filenames for each agent.
        """
        return [f"{name}.pdf" for name in self.agent_display_names]
    
    def generate_one(self, agent_id: str):
        agent_display_name = self.get_agent_display_name(agent_id=agent_id)
        self.add_to_log(f"Generating report for {agent_display_name}...")
        context = self.get_context(agent_id)
        # self.generate_report(context, agent_id)
        build_pdf(context, f"{self.get_agent_display_name(agent_id)}.pdf")
        
    def get_context(self, agent_id: str):
        context = {
            "injectors":[]
        }
        report_gen_time = self.period_to
        
        self.period_from = self.period_to - timedelta(minutes=60)
        # print("period_from: ", self.period_from)
        # print("period_to: ", self.period_to)
        
        # print("period_from timestamp (for self.timezone): ", self.period_from.astimezone(self.for_timezone).timestamp())
        # print("period_to timestamp (for self.timezone): ", self.period_to.astimezone(self.for_timezone).timestamp())
        
        data = self.retrieve_data(self.period_from.astimezone(self.for_timezone), self.period_to.astimezone(self.for_timezone), agent_id)
        data = data[-1]["payload"]
        reconciliation_state = find_reconciliation(data["state"])
        children = reconciliation_state["children"]
        
        # date and time
        # time on the report used to be when the report was generated.
        # now = datetime.now(ZoneInfo(reconciliation_state["timezone"]))
        report_gen_time_saudi = self.period_to.astimezone(ZoneInfo("Asia/Riyadh"))
        # report_gen_time_saudi = self.period_to
        report_date = report_gen_time_saudi.strftime("%d-%m-%Y")
        report_time = report_gen_time_saudi.strftime("%I:%M:%p").lower()
        context["report_date"] = report_date
        context["report_time"] = report_time
        
        # skid name
        context["skid_name"] = self.get_agent_display_name(agent_id)
        
        # injectors
        for injector in reconciliation_state["injectors"]:
            injector_name = injector["name"]
            injector_display_name = injector["displayName"]
            injector_index = injector["index"]
            
            flowmeter_total_name = f"{injector_name}_header_LDayTotal"
            actual_injection_detergent_name = f"{injector_name}_LDayTotal"
            calculated_detergent_name = f"{injector_name}CalcedLTotal"
            difference_name = f"{injector_name}Difference"
            
            sub_context = {
                "index": injector_index,
                "injector_name": injector_display_name,
                "flowmeter_total": children.get(flowmeter_total_name, {}).get("currentValue", 0),#injector["flowmeter_total"],
                "actual_injection_detergent": children.get(actual_injection_detergent_name, {}).get("currentValue", 0),#injector["actual_injection_detergent"],
                "calculated_detergent": children.get(calculated_detergent_name, {}).get("currentValue", 0),#injector["calculated_detergent"],
                "difference": children.get(difference_name, {}).get("currentValue", 0),#injector["difference"],
            }
            context["injectors"].append(sub_context)
        
        # totals
        context["total_gasoline"] = children.get("GasTotal", {}).get("currentValue", 0)
        context["total_calculated_detergent"] = children.get("CalcedInjectedTotal", {}).get("currentValue", 0)
        context["total_actual_detergent_injected"] = children.get("ActualInjectedTotal", {}).get("currentValue", 0)
        context["difference"] = children.get("Difference", {}).get("currentValue", 0)
        return context

if __name__ == "__main__":
    print("Generating PDF...")

generator = InjectorReportGenerator