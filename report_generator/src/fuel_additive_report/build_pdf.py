# requirements: fpdf2
# pip install fpdf2
import os
from pathlib import Path

from fpdf import FPDF

# ---------------------------
# Configurable inputs
# ---------------------------

class PDF(FPDF):
    # Theme
    BRAND_RGB = (2, 158, 87)         # #029E57
    BORDER_RGB = (226, 226, 226)     # #e2e2e2
    MUTED_RGB = (102, 102, 102)      # #666
    CARD_BG = (255, 255, 255)
    PAGE_MARGIN_MM = 16
    LOGO_PATH = str(Path(__file__).parent / "ZGH_logon.png.webp")
    
    def __init__(self, skid_name, report_time, report_date, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skid_name = skid_name
        self.report_time = report_time
        self.report_date = report_date
    
    def header(self):
        # three columns: logo | centered title | time/date boxes
        self.set_xy(self.PAGE_MARGIN_MM, self.PAGE_MARGIN_MM)
        col_w = (210 - 2*self.PAGE_MARGIN_MM) / 3.0  # A4 width = 210mm

        # Left: Logo (if provided) or placeholder text
        if self.LOGO_PATH and os.path.exists(self.LOGO_PATH):
            self.image(self.LOGO_PATH, x=self.PAGE_MARGIN_MM + (col_w-50)/2, y=self.PAGE_MARGIN_MM, w=50)
        else:
            # simple placeholder
            self.set_font("Helvetica", "B", 20)
            self.set_text_color(40, 130, 90)
            self.set_xy(self.PAGE_MARGIN_MM + 5, self.PAGE_MARGIN_MM + 12)
            self.cell(col_w-10, 10, "Zamil Group", align="C")

        # Middle: Title + Skid
        self.set_text_color(0, 0, 0)
        self.set_xy(self.PAGE_MARGIN_MM + col_w, self.PAGE_MARGIN_MM + 2)
        self.set_font("Helvetica", "B", 16)
        self.cell(col_w, 8, "RECONCILIATION", align="C", new_y="NEXT", new_x="LMARGIN")
        # skid line
        self.set_xy(self.PAGE_MARGIN_MM + col_w, self.PAGE_MARGIN_MM + 12)
        skid_text = f"Skid: {self.skid_name}" if self.skid_name else "Skid:"
        # A wordy skid name outgrows the middle column and runs over the
        # logo and the date boxes. Step the size down until it fits.
        size = 12
        self.set_font("Helvetica", "", size)
        while size > 7 and self.get_string_width(skid_text) > col_w:
            size -= 0.5
            self.set_font("Helvetica", "", size)
        self.cell(col_w, 6, skid_text, align="C")

        # Right: Time/Date boxed fields
        def meta(label, value, y):
            x = self.PAGE_MARGIN_MM + col_w*2 + 20
            self.set_xy(x-20, y)
            self.set_font("Helvetica", "", 11)
            self.cell(18, 8, f"{label} :", align="R")
            
            # Draw rounded rectangle for the grey box
            radius = 1.5
            self.set_draw_color(*self.BORDER_RGB)
            self.set_fill_color(245, 245, 245)
            
            # Draw the rounded rectangle using ellipse method
            # Top-left corner
            self.ellipse(x, y, radius * 2, radius * 2, style="DF")
            # Top-right corner  
            self.ellipse(x + 30 - radius * 2, y, radius * 2, radius * 2, style="DF")
            # Bottom-right corner
            self.ellipse(x + 30 - radius * 2, y + 8 - radius * 2, radius * 2, radius * 2, style="DF")
            # Bottom-left corner
            self.ellipse(x, y + 8 - radius * 2, radius * 2, radius * 2, style="DF")
            
            # Fill the center areas
            self.rect(x + radius, y, 30 - 2 * radius, 8, style="F")
            self.rect(x, y + radius, 30, 8 - 2 * radius, style="F")
            
            # Draw the border lines to complete the rounded rectangle
            self.line(x + radius, y, x + 30 - radius, y)  # top
            self.line(x + radius, y + 8, x + 30 - radius, y + 8)  # bottom
            self.line(x, y + radius, x, y + 8 - radius)  # left
            self.line(x + 30, y + radius, x + 30, y + 8 - radius)  # right
            
            self.set_xy(x, y+1.5)
            self.set_font("Helvetica", "", 11)
            self.cell(30, 5, value, align="C")

        meta("Time", self.report_time, self.PAGE_MARGIN_MM + 2)
        meta("Date", self.report_date, self.PAGE_MARGIN_MM + 12)

        # Move cursor below header
        self.set_y(self.PAGE_MARGIN_MM + 36)

    def rounded_rect(self, x, y, w, h, radius=3):
        # Create rounded rectangle with proper border
        self.set_draw_color(*self.BORDER_RGB)
        self.set_fill_color(*self.CARD_BG)
        
        # Draw the main rectangle with rounded corners using ellipse method
        # Top-left corner
        self.ellipse(x, y, radius * 2, radius * 2, style="DF")
        # Top-right corner  
        self.ellipse(x + w - radius * 2, y, radius * 2, radius * 2, style="DF")
        # Bottom-right corner
        self.ellipse(x + w - radius * 2, y + h - radius * 2, radius * 2, radius * 2, style="DF")
        # Bottom-left corner
        self.ellipse(x, y + h - radius * 2, radius * 2, radius * 2, style="DF")
        
        # Fill the center areas
        self.rect(x + radius, y, w - 2 * radius, h, style="F")
        self.rect(x, y + radius, w, h - 2 * radius, style="F")
        
        # Draw the border lines to complete the rounded rectangle
        self.line(x + radius, y, x + w - radius, y)  # top
        self.line(x + radius, y + h, x + w - radius, y + h)  # bottom
        self.line(x, y + radius, x, y + h - radius)  # left
        self.line(x + w, y + radius, x + w, y + h - radius)  # right

    def divider(self, x1, y, x2):
        self.set_draw_color(*self.BRAND_RGB)
        self.line(x1, y, x2, y)
        self.set_draw_color(*self.BORDER_RGB)

    def label_pair(self, top, bottom, x, y, w):
        self.set_xy(x, y)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 0, 0)
        self.cell(w, 4, top, new_y="NEXT")
        self.set_x(x)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*self.MUTED_RGB)
        self.cell(w, 4, bottom, new_y="NEXT")

    def number_with_unit(self, value, unit, x, y, w, h=8):
        # Single rounded rectangle with value on left and unit on right
        self.set_draw_color(*self.BORDER_RGB)
        self.set_fill_color(248, 248, 248)
        
        # Draw rounded rectangle using ellipse method
        radius = 1.5
        # Top-left corner
        self.ellipse(x, y, radius * 2, radius * 2, style="DF")
        # Top-right corner  
        self.ellipse(x + w - radius * 2, y, radius * 2, radius * 2, style="DF")
        # Bottom-right corner
        self.ellipse(x + w - radius * 2, y + h - radius * 2, radius * 2, radius * 2, style="DF")
        # Bottom-left corner
        self.ellipse(x, y + h - radius * 2, radius * 2, radius * 2, style="DF")
        
        # Fill the center areas
        self.rect(x + radius, y, w - 2 * radius, h, style="F")
        self.rect(x, y + radius, w, h - 2 * radius, style="F")
        
        # Draw the border lines to complete the rounded rectangle
        self.line(x + radius, y, x + w - radius, y)  # top
        self.line(x + radius, y + h, x + w - radius, y + h)  # bottom
        self.line(x, y + radius, x, y + h - radius)  # left
        self.line(x + w, y + radius, x + w, y + h - radius)  # right
        
        # Value on the left
        self.set_xy(x+2, y+1.4)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(0,0,0)
        self.cell(w-12, h-2.8, value, align="L")
        
        # Unit on the right
        self.set_xy(x+w-10, y+1.4)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.MUTED_RGB)
        self.cell(8, h-2.8, unit, align="R")

def build_pdf(context: dict) -> bytes:
    """Render the reconciliation report PDF and return its bytes."""
    skid_name = context["skid_name"]
    report_time = context["report_time"]
    report_date = context["report_date"]
    
    INJECTORS = []
    for injector in context["injectors"]:
        INJECTORS.append((
            injector["injector_name"], 
            str(injector["flowmeter_total"]), 
            str(injector["actual_injection_detergent"]), 
            str(injector["calculated_detergent"]), 
            str(injector["difference"])
        ))

    TOTALS = {
        "Gasoline": str(context["total_gasoline"]),
        "Calc. Detergent": str(context["total_calculated_detergent"]),
        "Act. Detergent": str(context["total_actual_detergent_injected"]),
        "Difference": str(context["difference"]),
    }
    
    pdf = PDF(skid_name, report_time, report_date, format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=pdf.PAGE_MARGIN_MM)
    pdf.add_page()

    # Card grid: 2 columns x N rows (here 6 cards -> 3 rows)
    left = pdf.PAGE_MARGIN_MM
    right = 210 - pdf.PAGE_MARGIN_MM
    gutter = 6
    card_w = (right - left - gutter) / 2.0
    card_h = 54

    def render_injector(i, inj_title, gasoline, act_det, calc_det, diff, x, y):
        pdf.rounded_rect(x, y, card_w, card_h)
        # title
        pdf.set_xy(x+6, y+6)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(0,0,0)
        pdf.cell(card_w-12, 5, inj_title, new_y="NEXT")
        # divider
        pdf.divider(x+6, y+13, x+card_w-6)

        # two columns inside
        inner_gap = 8
        col_w = (card_w - 12 - inner_gap) / 2.0
        c1x = x + 6
        c2x = c1x + col_w + inner_gap
        top_y = y + 16

        # Header Total/Gasoline
        pdf.label_pair("Header Total", "Gasoline", c1x, top_y, col_w)
        pdf.number_with_unit(gasoline, "L", c1x, top_y + 9, col_w)

        # Injection Total/Detergent
        pdf.label_pair("Injection Total", "Detergent", c2x, top_y, col_w)
        pdf.number_with_unit(act_det, "L", c2x, top_y + 9, col_w)

        # Bottom metrics (Calc Det / Difference)
        base_y = top_y + 19
        pdf.set_xy(c1x, base_y)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 4, "Calc. Detergent", new_y="NEXT")
        pdf.number_with_unit(calc_det, "L", c1x, base_y + 5, col_w)

        pdf.set_xy(c2x, base_y)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(40, 4, "Difference", new_y="NEXT")
        pdf.number_with_unit(diff, "%", c2x, base_y + 5, col_w)

    # Place injector cards
    y = pdf.get_y() - 5  # Raise by 5mm
    for idx, (title, gas, act, calc, dlt) in enumerate(INJECTORS):
        row = idx // 2
        col = idx % 2
        x = left + col*(card_w + gutter)
        y_card = y + row*(card_h + gutter)
        render_injector(idx, title, gas, act, calc, dlt, x, y_card)

    # Totals section
    # compute Y under the last row
    rows = (len(INJECTORS)+1)//2
    tot_y = y + rows*(card_h + gutter) + 10
    pdf.rounded_rect(left, tot_y, right-left, 43)

    pdf.set_xy(left+10, tot_y+8)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0,0,0)
    pdf.cell(0, 6, "Reconciliation Totals", new_y="NEXT")
    pdf.divider(left+10, tot_y+16, right-10)

    # 4 equal columns
    grid_x = left + 10
    grid_y = tot_y + 20
    grid_w = right - left - 20
    col_w = (grid_w / 4.0) * 0.9  # Make columns 10% narrower
    spacing = (grid_w - (col_w * 4)) / 3  # Calculate spacing between columns

    headers_units = [
        ("Gasoline", "L"),
        ("Calc. Detergent", "L"),
        ("Act. Detergent", "L"),
        ("Difference", "%"),
    ]

    for i, (hdr, unit) in enumerate(headers_units):
        x = grid_x + i*(col_w + spacing)
        # label
        pdf.set_xy(x, grid_y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(0,0,0)
        pdf.cell(col_w, 5, hdr, new_y="NEXT")
        # value
        val = TOTALS[hdr]
        pdf.number_with_unit(val, unit, x, grid_y + 7, col_w)

    return bytes(pdf.output())
