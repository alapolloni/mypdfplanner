#!/Users/apolloni/py_mypdfplanner/bin/python
from fpdf import FPDF, XPos, YPos
import calendar
from datetime import datetime
import argparse

class CalendarPDF(FPDF):
    def header(self):
        pass
    
    def footer(self):
        pass

def draw_dot_pattern(pdf, x, y, width, height, dot_spacing=5):
    """Draw a square dot pattern in the specified area"""
    dot_size = 0.5
    current_y = y + dot_spacing
    while current_y < y + height:
        current_x = x + dot_spacing
        while current_x < x + width:
            pdf.circle(current_x, current_y, dot_size, 'F')
            current_x += dot_spacing
        current_y += dot_spacing

def create_monthly_calendar(year, month):
    # Create PDF in A5 size (148 x 210 mm)
    pdf = CalendarPDF(orientation='P', unit='mm', format='A5')
    
    # Get calendar data
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Define margins
    left_margin = 5
    right_margin = 5
    available_width = 148 - left_margin - right_margin
    
    # LEFT PAGE - Weekdays (Mon-Fri)
    pdf.add_page()
    pdf.set_auto_page_break(False)
    
    # Title for left page - smaller, aligned top left at margin
    pdf.set_font('Helvetica', 'B', 11)
    pdf.text(left_margin, 10, f'{month_name} {year}')
    
    # Day headers for weekdays
    pdf.set_font('Helvetica', '', 10)
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    
    cell_width = available_width / 5  # 5 weekdays
    
    # Calculate cell height to fit calendar down to review section
    review_y = 210 - 25  # Review section position
    header_y = 18  # Where day headers start (closer to title)
    available_height = review_y - header_y - 8  # 8mm for day headers
    cell_height = available_height / len(cal)  # Divide by number of weeks
    
    pdf.set_xy(left_margin, header_y)
    for day in weekdays:
        pdf.cell(cell_width, 8, day, border=0, align='C')
    pdf.set_xy(left_margin, pdf.get_y() + 8)
    
    # Calendar grid for weekdays
    pdf.set_font('Helvetica', '', 10)
    pdf.set_draw_color(211, 211, 211)  # Light grey for borders
    for week in cal:
        pdf.set_x(left_margin)
        # Only Mon-Fri (indices 0-4)
        for i in range(5):
            day = week[i]
            if day == 0:
                # Shade empty cells very light grey
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.set_fill_color(245, 245, 245)  # Very light grey
                pdf.rect(x, y, cell_width, cell_height, 'FD')
                pdf.set_xy(x + cell_width, y)
            else:
                x = pdf.get_x()
                y = pdf.get_y()
                
                pdf.rect(x, y, cell_width, cell_height)
                pdf.set_xy(x + 2, y + 2)
                pdf.cell(cell_width - 2, 5, str(day), align='L')
                pdf.set_xy(x + cell_width, y)
        pdf.set_xy(left_margin, pdf.get_y() + cell_height)
    
    # Add review checklist at bottom left
    review_y = 210 - 25  # 25mm from bottom
    pdf.set_font('Helvetica', 'B', 10)
    checkbox_size = 3
    checkbox_margin = 2
    
    # Position "Review" aligned with the left edge of checkboxes
    pdf.set_xy(left_margin, review_y)
    pdf.cell(0, 5, 'Review', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.set_font('Helvetica', '', 9)
    items = ['Goals', 'Yearly Spread', 'Highlights']
    
    for item in items:
        current_y = pdf.get_y()
        # Draw checkbox
        pdf.rect(left_margin, current_y, checkbox_size, checkbox_size)
        # Add text
        pdf.set_xy(left_margin + checkbox_size + checkbox_margin, current_y)
        pdf.cell(0, checkbox_size, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # RIGHT PAGE - Weekend (Sat-Sun)
    pdf.add_page()
    
    # Day headers for weekend
    pdf.set_font('Helvetica', '', 10)
    weekend = ['Sat', 'Sun']
    
    # Use same cell width as weekdays for consistency
    cell_width_weekend = cell_width  # Same width as weekday cells
    weekend_width = cell_width_weekend * 2  # 2 weekend days
    
    # Adjust sections width to use remaining space
    sections_width = available_width - weekend_width
    
    pdf.set_xy(left_margin, header_y)
    for day in weekend:
        pdf.cell(cell_width_weekend, 8, day, border=0, align='C')
    pdf.set_xy(left_margin, pdf.get_y() + 8)
    
    # Calendar grid for weekend
    pdf.set_font('Helvetica', '', 10)
    pdf.set_draw_color(211, 211, 211)  # Light grey for borders
    weekend_end_y = pdf.get_y()  # Track where weekend calendar ends
    for week in cal:
        pdf.set_x(left_margin)
        # Only Sat-Sun (indices 5-6)
        for i in range(5, 7):
            day = week[i]
            if day == 0:
                # Shade empty cells very light grey
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.set_fill_color(245, 245, 245)  # Very light grey
                pdf.rect(x, y, cell_width_weekend, cell_height, 'FD')
                pdf.set_xy(x + cell_width_weekend, y)
            else:
                x = pdf.get_x()
                y = pdf.get_y()
                
                pdf.rect(x, y, cell_width_weekend, cell_height)
                pdf.set_xy(x + 2, y + 2)
                pdf.cell(cell_width_weekend - 2, 5, str(day), align='L')
                pdf.set_xy(x + cell_width_weekend, y)
        weekend_end_y = pdf.get_y() + cell_height
        pdf.set_xy(left_margin, weekend_end_y)
    
    # Add sections to the right of weekend (Goal, Tasks, Other)
    sections_x = left_margin + weekend_width
    sections_y = 18  # Start at same height as day headers
    section_height = (len(cal) * cell_height + 8) / 3  # Divide space including header row into 3
    
    sections = ['Goal', 'Tasks', 'Other']
    header_height = 8
    
    for i, section in enumerate(sections):
        section_y = sections_y + (i * section_height)
        
        # Draw header with light grey background
        pdf.set_fill_color(211, 211, 211)  # Light grey
        pdf.set_text_color(0, 0, 0)  # Black text
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(sections_x, section_y)
        pdf.cell(sections_width, header_height, section, border=0, align='C', fill=True)
        
        # Draw dot pattern below header (no border)
        content_height = section_height - header_height
        content_y = section_y + header_height
        draw_dot_pattern(pdf, sections_x, content_y, sections_width, content_height)
    
    # Add dot pattern below weekend days - full width across the page
    page_bottom = 210 - 5  # A5 height minus bottom margin
    weekend_dot_height = page_bottom - weekend_end_y
    if weekend_dot_height > 5:  # Only draw if there's meaningful space
        draw_dot_pattern(pdf, left_margin, weekend_end_y, available_width, weekend_dot_height)
    
    # Reset text color
    pdf.set_text_color(0, 0, 0)
    
    # Save the PDF
    filename = f'calendar_{year}_{month:02d}.pdf'
    pdf.output(filename)
    print(f'Calendar saved as {filename}')
    return filename

# Example: Create calendar for current month
now = datetime.now()

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate an A5 monthly calendar PDF')
parser.add_argument('--year-month', type=str, 
                    help='Year and month in YYYY-MM format (e.g., 2025-01)',
                    default=f'{now.year}-{now.month:02d}')

args = parser.parse_args()

# Parse the year-month argument
try:
    year, month = map(int, args.year_month.split('-'))
    if not (1 <= month <= 12):
        raise ValueError("Month must be between 1 and 12")
    create_monthly_calendar(year, month)
except ValueError as e:
    print(f"Error: Invalid year-month format. Use YYYY-MM (e.g., 2025-01)")
    print(f"Details: {e}")

# Or create for a specific month directly in code:
# create_monthly_calendar(2025, 1)  # January 2025