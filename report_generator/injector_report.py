import os
import sys
from pprint import pprint

## Add the include directory to the path if it is not already there.
include_dir = os.path.join(os.path.dirname(__file__), 'include')
if not include_dir in sys.path:
    sys.path.append(include_dir)
    
from pydoover.reports.base import ReportGenerator
from jinja2 import Template
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
from datetime import datetime
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
        self.generate_report(context, agent_id)
        
    def get_context(self, agent_id: str):
        context = {
            "injectors":[]
        }
        agg = self.get_current_data_aggregate(agent_id)
        reconciliation_state = find_reconciliation(agg["state"])
        children = reconciliation_state["children"]
        
        # date and time
        now = datetime.now(ZoneInfo(reconciliation_state["timezone"]))
        report_date = now.strftime("%d-%m-%Y")
        report_time = now.strftime("%I:%M:%p").lower()
        context["report_date"] = report_date
        context["report_time"] = report_time
        
        # skid name
        context["skid_name"] = reconciliation_state["skid_name"]
        
        # injectors
        for injector in reconciliation_state["injectors"]:
            injector_name = injector["name"]
            injector_display_name = injector["displayName"]
            injector_index = injector["index"]
            
            flowmeter_total_name = f"{injector_name}_LDayTotal"
            actual_injection_detergent_name = f"{injector_name}_header_LDayTotal"
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
    
    def generate_report(self, context: dict, agent_id: str):
    
    # Read the HTML template
        with open('injector-report.html.template', 'r', encoding='utf-8') as file:
            template_content = file.read()
        
        # Create Jinja2 template and render with context
        template = Template(template_content)
        rendered_html = template.render(**context)
        
        # Save the rendered HTML to file
        with open('injector-report.html', 'w', encoding='utf-8') as f:
            f.write(rendered_html)
        print("Rendered HTML saved to injector-report.html")
        
        # Replace CSS custom properties with direct values to avoid WeasyPrint issues
        rendered_html = rendered_html.replace('var(--bg)', '#fafafa')
        rendered_html = rendered_html.replace('var(--ink)', '#111')
        rendered_html = rendered_html.replace('var(--muted)', '#666')
        rendered_html = rendered_html.replace('var(--brand)', '#029E57')
        rendered_html = rendered_html.replace('var(--card)', '#fff')
        rendered_html = rendered_html.replace('var(--border)', '#e2e2e2')
        rendered_html = rendered_html.replace('var(--radius)', '12px')
        rendered_html = rendered_html.replace('var(--pad)', '24px')
        rendered_html = rendered_html.replace('var(--maxw)', '1600px')
        rendered_html = rendered_html.replace('var(--font)', 'Helvetica, Arial, sans-serif')
        
        # Add portrait CSS directly to the HTML head
        portrait_css_inline = '''
            <style>
            @page {
                size: A4 portrait !important;
                margin: 16mm !important;
            }
            /* Force all text to be black and visible */
            body *{color:black !important}
            .number, .input, .summary .number{color:#000 !important; opacity:1 !important}
            .value{color:#000 !important; opacity:1 !important; visibility:visible !important}
            .number .value{color:#000 !important; opacity:1 !important; visibility:visible !important}
            .input{color:#000 !important; opacity:1 !important; visibility:visible !important}
            /* Force reliable fonts for numbers */
            .number, .input, .value{font-family: Helvetica, Arial, sans-serif !important}
            /* Ensure text rendering */
            *{text-rendering:optimizeLegibility !important}
            </style>
        '''
        
        # Insert the portrait CSS into the head section
        rendered_html = rendered_html.replace('</head>', portrait_css_inline + '</head>')
        
        # Configure fonts
        font_config = FontConfiguration()
        
        # Create HTML object and generate PDF with additional options
        html_doc = HTML(string=rendered_html)
        pdf_bytes = html_doc.write_pdf(
            font_config=font_config,
            presentational_hints=True,
            zoom=1,
            optimize_images=False
        )
        
        # Save the PDF
        output_filename = f'{agent_id}.pdf'
        with open(output_filename, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"PDF generated successfully: {output_filename}")
        return output_filename

if __name__ == "__main__":
    print("Generating PDF...")

generator = InjectorReportGenerator