import os
import sys

## Add the include directory to the path if it is not already there.
include_dir = os.path.join(os.path.dirname(__file__), 'include')
if not include_dir in sys.path:
    sys.path.append(include_dir)
    
from pydoover.reports.base import ReportGenerator
from jinja2 import Template
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

class InjectorReportGenerator(ReportGenerator):
    def __init__(self):
        pass
    
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
        
    def get_context(self, agent_id: str):
        agg = self.get_current_data_aggregate(agent_id)
        reconciliation_state = self.find_reconciliation(agg["state"])
        
        
        
        
        context = {}
        return context
    
    
        
    def generate_report(self):
    
    # Read the HTML template
        with open('injector-report.html', 'r', encoding='utf-8') as file:
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
        output_filename = 'injector-report.pdf'
        with open(output_filename, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"PDF generated successfully: {output_filename}")
        return output_filename
    
    @staticmethod
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


context = {
  "report_date": "19-08-2025",
  "report_time": "14:30:00",
  "skid_name": "ZN-123",
  "injectors": [
    {
      "index": 1,
      "injector_name": "INJ-001",
      "flowmeter_total": 12345.67,
      "actual_injection_detergent": 89.01,
      "calculated_detergent": 88.5,
      "difference": 0.58,
    },
    {
      "index": 2,
      "injector_name": "INJ-002",
      "flowmeter_total": 23456.78,
      "actual_injection_detergent": 76.54,
      "calculated_detergent": 77.0,
      "difference": -0.60,
    },
    {
      "index": 3,
      "injector_name": "INJ-003",
      "flowmeter_total": 34567.89,
      "actual_injection_detergent": 65.43,
      "calculated_detergent": 66.0,
      "difference": -0.86,
    },
    {
      "index": 4,
      "injector_name": "INJ-004",
      "flowmeter_total": 45678.90,
      "actual_injection_detergent": 54.32,
      "calculated_detergent": 55.0,
      "difference": -1.24,
    },
    {
      "index": 5,
      "injector_name": "INJ-005",
      "flowmeter_total": 56789.01,
      "actual_injection_detergent": 43.21,
      "calculated_detergent": 44.0,
      "difference": -1.80,
    },
    {
      "index": 6,
      "injector_name": "INJ-006",
      "flowmeter_total": 67890.12,
      "actual_injection_detergent": 32.10,
      "calculated_detergent": 33.0,
      "difference": -2.73,
    },
  ],
  "total_gasoline": 240627.37,
  "total_calculated_detergent": 363.50,
  "total_actual_detergent_injected": 360.61,
  "difference": -0.80,
}

def generate_pdf():
    # Read the HTML template
    with open('3-injector-report.html', 'r', encoding='utf-8') as file:
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
    output_filename = 'injector-report.pdf'
    with open(output_filename, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"PDF generated successfully: {output_filename}")
    return output_filename

if __name__ == "__main__":
    print("Generating PDF...")
    # generate_pdf()


generator = InjectorReportGenerator