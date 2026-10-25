from fpdf import FPDF, XPos, YPos
import calendar
from datetime import datetime
import argparse

class CalendarPDF(FPDF):
    def header(self):
        pass
    
    def footer(self):
        pass

def create_monthly_calendar(year, month):
    # Create PDF in A5 size (148 x 210 mm)
    pdf = CalendarPDF(orientation='P', unit='mm', format='A5')
    pdf.add_page()
    pdf.set_auto_page_break(False)
    
    # Title
    pdf.set_font('Helvetica', 'B', 20)
    month_name = calendar.month_name[month]
    pdf.cell(0, 0, f'{month_name} {year}', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Get calendar data
    cal = calendar.monthcalendar(year, month)
    
    # Day headers
    pdf.set_font('Helvetica', 'B', 10)
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    # Calculate margins and cell sizes to fit page
    left_margin = 5
    right_margin = 5
    available_width = 148 - left_margin - right_margin  # A5 width minus margins
    cell_width = available_width / 7
    cell_height = 36
    
    pdf.set_xy(left_margin, 15)
    for day in days:
        pdf.cell(cell_width, 8, day, border=1, align='C')
    pdf.set_xy(left_margin, pdf.get_y() + 8)
    
    # Calendar grid
    pdf.set_font('Helvetica', '', 10)
    for week in cal:
        pdf.set_x(left_margin)
        for day in week:
            if day == 0:
                pdf.cell(cell_width, cell_height, '', border=1)
            else:
                # Save current position
                x = pdf.get_x()
                y = pdf.get_y()
                
                # Draw cell border
                pdf.rect(x, y, cell_width, cell_height)
                
                # Place day number in top-right corner
                pdf.set_xy(x, y + 2)
                pdf.cell(cell_width + .5 , 0, str(day), align='R')
                
                # Move to next cell
                pdf.set_xy(x + cell_width, y)
        pdf.set_xy(left_margin, pdf.get_y() + cell_height)
    
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