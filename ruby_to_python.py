#!/usr/bin/env python3

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from datetime import datetime, timedelta
import sys
import math

# Constants
WEEKS = 1
HOUR_LABELS = [None, None, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, None]
HOUR_COUNT = len(HOUR_LABELS)
COLUMN_COUNT = 4
LIGHT_COLOR = HexColor('#AAAAAA')
MEDIUM_COLOR = HexColor('#888888')
DARK_COLOR = HexColor('#000000')
DATE_LONG = "%B %-d, %Y"
FILE_NAME = "time_block_pages.pdf"
PAGE_SIZE = A4
# Order is left, bottom, right, top (ReportLab convention)
LEFT_PAGE_MARGINS = [36, 36, 72, 36]  # left, bottom, right, top
RIGHT_PAGE_MARGINS = [72, 36, 36, 36]  # left, bottom, right, top


def business_days_between(start_date, end_date):
    """
    Calculates the number of business days in range (start_date, end_date]
    """
    days_between = (end_date - start_date).days
    if days_between <= 0:
        return 0
    
    whole_weeks, extra_days = divmod(days_between, 7)
    
    if extra_days != 0:
        tomorrow = start_date + timedelta(days=1)
        if tomorrow.weekday() <= end_date.weekday():
            sunday_count = 1 if tomorrow.weekday() == 6 else 0
            saturday_count = 1 if end_date.weekday() == 5 else 0
            extra_days -= (sunday_count + saturday_count)
        else:
            extra_days -= 2
    
    return (whole_weeks * 5) + extra_days


def business_days_left_in_year(date):
    """Calculate business days left in the year"""
    year_end = datetime(date.year, 12, 31).date()
    days = business_days_between(date, year_end)
    
    if days == 0:
        return "last work day of the year"
    elif days == 1:
        return "1 work day left in the year"
    else:
        return f"{days} work days in the year"


def business_days_left_in_sprint(date):
    """Calculate business days left in current sprint"""
    if date.day <= 15:
        sprint_end = datetime(date.year, date.month, 15).date()
    else:
        # Last day of month
        next_month = date.replace(day=28) + timedelta(days=4)
        sprint_end = (next_month - timedelta(days=next_month.day)).date()
    
    days = business_days_between(date, sprint_end)
    
    if days == 0:
        return "last day of sprint"
    elif days == 1:
        return "1 day left in sprint"
    else:
        return f"{days} days left in sprint"


def quarter(date):
    """Get the quarter (1-4) for a given date"""
    return math.ceil(date.month / 3.0)


class PlannerPDF:
    def __init__(self, filename):
        self.filename = filename
        self.c = canvas.Canvas(filename, pagesize=PAGE_SIZE)
        self.page_width, self.page_height = PAGE_SIZE
        self.current_margins = RIGHT_PAGE_MARGINS
        self.grid = None
        
        # Try to register Helvetica Neue if available, otherwise use Helvetica
        try:
            pdfmetrics.registerFont(TTFont('Helvetica-Neue', 'HelveticaNeue.ttc'))
            pdfmetrics.registerFont(TTFont('Helvetica-Neue-Bold', 'HelveticaNeue-Bold.ttc'))
            self.font_name = 'Helvetica-Neue'
            self.font_bold = 'Helvetica-Neue-Bold'
        except:
            self.font_name = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'
        
        self.c.setStrokeColor(MEDIUM_COLOR)
        self.c.setLineWidth(0.5)
    
    def define_grid(self, columns, rows, gutter=0):
        """Define a grid system for layout"""
        left, bottom, right, top = self.current_margins
        width = self.page_width - left - right
        height = self.page_height - bottom - top
        
        col_width = width / columns
        row_height = height / rows
        
        self.grid = {
            'columns': columns,
            'rows': rows,
            'col_width': col_width,
            'row_height': row_height,
            'gutter': gutter,
            'left': left,
            'top': top,
            'width': width,
            'height': height
        }
    
    def grid_box(self, row, col, row_span=1, col_span=1):
        """Get bounding box coordinates for grid cell(s) - returns bottom-left x, y and dimensions"""
        g = self.grid
        x = g['left'] + col * g['col_width']
        # Calculate from top of page, going down
        y_from_top = g['top'] + row * g['row_height']
        # Convert to bottom-left coordinate system
        y = self.page_height - y_from_top - row_span * g['row_height']
        width = col_span * g['col_width']
        height = row_span * g['row_height']
        return (x, y, width, height)
    
    def draw_checkbox(self, x, y, size, padding):
        """Draw a checkbox with dashed border"""
        self.c.saveState()
        self.c.setStrokeColor(LIGHT_COLOR)
        self.c.setDash([1, 2], 0.5)
        self.c.rect(x + padding, y + padding, size, size)
        self.c.restoreState()
    
    def begin_new_page(self, side):
        """Start a new page with appropriate margins"""
        if hasattr(self, '_page_started'):
            self.c.showPage()
        
        self.current_margins = LEFT_PAGE_MARGINS if side == 'left' else RIGHT_PAGE_MARGINS
        self.c.setStrokeColor(MEDIUM_COLOR)
        self.c.setLineWidth(0.5)
        
        if side == 'right':
            self.hole_punches()
        
        self._page_started = True
    
    def hole_punches(self):
        """Draw hole punch marks"""
        x = 25
        for y in [1.25 * inch, 5.5 * inch, 9.75 * inch]:
            self.c.line(x - 5, y, x + 5, y)
            self.c.line(x, y - 5, x, y + 5)
    
    def week_ahead_page(self, first_day, last_day):
        """Generate the week ahead overview page"""
        self.hole_punches()
        
        header_row_count = 2
        body_row_count = HOUR_COUNT * 2
        first_column = 0
        last_column = COLUMN_COUNT - 1
        first_row = header_row_count
        last_row = header_row_count + body_row_count - 1
        
        self.define_grid(columns=COLUMN_COUNT, rows=header_row_count + body_row_count, gutter=0)
        
        # Header Left
        x, y, w, h = self.grid_box(0, first_column, 1, COLUMN_COUNT)
        self.c.setFont(self.font_bold, 20)
        self.c.drawString(x, y + h - 20, "The Week Ahead")
        
        x, y, w, h = self.grid_box(1, first_column, 1, COLUMN_COUNT)
        self.c.setFont(self.font_name, 10)
        self.c.setFillColor(MEDIUM_COLOR)
        date_range = f"{first_day.strftime('%A, %B %-d')} — {last_day.strftime('%A, %B %-d, %Y')}"
        self.c.drawString(x, y + h - 12, date_range)
        
        # Header Right
        x, y, w, h = self.grid_box(0, 3, 1, last_column - 3 + 1)
        self.c.setFont(self.font_bold, 20)
        self.c.setFillColor(DARK_COLOR)
        week_text = first_day.strftime("Week %W")
        self.c.drawRightString(x + w, y + h - 20, week_text)
        
        x, y, w, h = self.grid_box(1, 3, 1, last_column - 3 + 1)
        self.c.setFont(self.font_name, 10)
        self.c.setFillColor(MEDIUM_COLOR)
        self.c.drawRightString(x + w, y + h - 12, f"Quarter {quarter(first_day)}")
        
        self.c.setFillColor(DARK_COLOR)
        
        # Horizontal lines - draw at bottom of each row
        for row in range(first_row, last_row + 1):
            x, y, w, h = self.grid_box(row, first_column, 1, last_column - first_column + 1)
            self.c.line(x, y, x + w, y)
        
        # Checkboxes
        checkbox_padding = 6
        checkbox_size = self.grid['row_height'] - (2 * checkbox_padding)
        for row in range(first_row + 1, last_row + 1):
            x, y, w, h = self.grid_box(row, 0)
            # Adjust checkbox to be at bottom of cell, accounting for height
            self.draw_checkbox(x, y + h - checkbox_size - 2*checkbox_padding, checkbox_size, checkbox_padding)
    
    def daily_tasks_page(self, date):
        """Generate daily tasks page"""
        self.begin_new_page('left')
        
        header_row_count = 2
        body_row_count = HOUR_COUNT * 2
        last_row = header_row_count + body_row_count - 1
        
        self.define_grid(columns=COLUMN_COUNT, rows=header_row_count + body_row_count, gutter=0)
        
        # Header
        left_header = date.strftime(DATE_LONG)
        right_header = date.strftime("%A")
        
        x, y, w, h = self.grid_box(0, 0, 2, 2)
        self.c.setFont(self.font_bold, 20)
        self.c.drawString(x, y + h - 20, left_header)
        
        x, y, w, h = self.grid_box(0, 2, 2, 2)
        self.c.drawRightString(x + w, y + h - 20, right_header)
        
        # Daily metrics box
        x, y, w, h = self.grid_box(1, 0, 4, 4)
        self.c.saveState()
        self.c.setDash([1, 2])
        self.c.rect(x, y, w, h)
        self.c.restoreState()
        
        self.c.setFont(self.font_name, 10)
        self.c.setFillColor(MEDIUM_COLOR)
        self.c.drawString(x + 10, y + h - 20, "Daily Metrics")
        
        # Shutdown checkbox
        self.c.rect(x + w - 20, y + 10, 10, 10)
        self.c.setFont(self.font_name, 9)
        self.c.drawRightString(x + w - 26, y + 12, "shutdown complete")
        
        self.c.setFillColor(DARK_COLOR)
        
        # Tasks / Notes labels
        x, y, w, h = self.grid_box(5, 0, 1, 2)
        self.c.setFont(self.font_bold, 10)
        self.c.drawString(x + 6, y + h/2 - 3, "Tasks:")
        
        x, y, w, h = self.grid_box(5, 2, 1, 2)
        self.c.drawString(x + 6, y + h/2 - 3, "Ideas:")
        
        # Horizontal lines
        for row in range(5, last_row + 1):
            x, y, w, h = self.grid_box(row, 0, 1, 4)
            self.c.line(x, y, x + w, y)
        
        # Vertical line
        x1, y1, w1, h1 = self.grid_box(6, 1, 1, 1)
        x2, y2, w2, h2 = self.grid_box(last_row, 1, 1, 1)
        self.c.saveState()
        self.c.setDash([1, 2], 2)
        self.c.line(x1 + w1, y1 + h1, x2 + w2, y2)
        self.c.restoreState()
        
        # Checkboxes
        checkbox_padding = 6
        checkbox_size = self.grid['row_height'] - (2 * checkbox_padding)
        for row in range(6, last_row + 1):
            x, y, w, h = self.grid_box(row, 0)
            self.draw_checkbox(x, y + h - checkbox_size - 2*checkbox_padding, checkbox_size, checkbox_padding)
    
    def daily_calendar_page(self, date):
        """Generate daily calendar page"""
        self.begin_new_page('right')
        
        header_row_count = 2
        body_row_count = HOUR_COUNT * 2
        first_column = 0
        last_column = COLUMN_COUNT - 1
        first_hour_row = header_row_count
        last_hour_row = header_row_count + body_row_count - 1
        
        self.define_grid(columns=COLUMN_COUNT, rows=header_row_count + body_row_count, gutter=0)
        
        # Header
        left_header = date.strftime(DATE_LONG)
        right_header = date.strftime("%A")
        left_subhed = date.strftime(f"Quarter {quarter(date)} Week %W Day %j")
        right_subhed = business_days_left_in_year(date)
        
        x, y, w, h = self.grid_box(0, first_column, 2, 2)
        self.c.setFont(self.font_bold, 20)
        self.c.drawString(x, y + h - 20, left_header)
        
        x, y, w, h = self.grid_box(0, 2, 1, last_column - 2 + 1)
        self.c.drawRightString(x + w, y + h - 20, right_header)
        
        x, y, w, h = self.grid_box(1, first_column, 1, COLUMN_COUNT)
        self.c.setFont(self.font_name, 10)
        self.c.setFillColor(MEDIUM_COLOR)
        self.c.drawString(x, y + h - 12, left_subhed)
        self.c.drawRightString(x + w, y + h - 12, right_subhed)
        
        self.c.setFillColor(DARK_COLOR)
        
        # Hour labels
        overhang = 24
        for hour in range(HOUR_COUNT):
            if HOUR_LABELS[hour]:
                x, y, w, h = self.grid_box(hour * 2 + first_hour_row, 0)
                self.c.setFont(self.font_name, 10)
                self.c.drawRightString(x - 4, y + h/2 - 3, str(HOUR_LABELS[hour]))
        
        # Horizontal lines
        self.c.setStrokeColor(MEDIUM_COLOR)
        
        # Top line of hour grid
        x, y, w, h = self.grid_box(first_hour_row, first_column, 1, COLUMN_COUNT)
        self.c.line(x - overhang, y + h, x + w, y + h)
        
        for row in range(first_hour_row, last_hour_row + 1, 2):
            # Half hour lines (dashed) - at bottom of first row
            x, y, w, h = self.grid_box(row, first_column, 1, COLUMN_COUNT)
            self.c.saveState()
            self.c.setDash([1, 2], 2)
            self.c.line(x - overhang, y, x + w, y)
            self.c.restoreState()
            
            # Hour lines (solid) - at bottom of second row
            if row + 1 <= last_hour_row:
                x, y, w, h = self.grid_box(row + 1, first_column, 1, COLUMN_COUNT)
                self.c.line(x - overhang, y, x + w, y)
        
        # Vertical lines
        for col in range(COLUMN_COUNT + 1):
            x1, y1, w1, h1 = self.grid_box(header_row_count, col if col < COLUMN_COUNT else COLUMN_COUNT - 1, 1, 1)
            x2, y2, w2, h2 = self.grid_box(last_hour_row, col if col < COLUMN_COUNT else COLUMN_COUNT - 1, 1, 1)
            
            self.c.saveState()
            self.c.setDash([1, 2], 2)
            if col == COLUMN_COUNT:
                self.c.line(x1 + w1, y1 + h1, x2 + w2, y2)
            else:
                self.c.line(x1, y1 + h1, x2, y2)
            self.c.restoreState()
    
    def weekend_page(self, saturday, sunday):
        """Generate weekend page"""
        self.begin_new_page('left')
        
        header_row_count = 2
        hour_row_count = HOUR_COUNT
        task_row_count = 2 * HOUR_COUNT - hour_row_count - 1
        body_row_count = header_row_count + task_row_count + hour_row_count
        
        # Create two columns for Saturday and Sunday
        left, bottom, right, top = self.current_margins
        page_width = self.page_width - left - right
        column_width = (page_width - 24) / 2  # 24 is gutter
        
        for idx, date in enumerate([saturday, sunday]):
            x_offset = left + idx * (column_width + 24)
            
            # Save state and work within this column
            self.c.saveState()
            
            # Temporarily adjust grid for this column
            old_margins = self.current_margins
            self.current_margins = [x_offset, bottom, self.page_width - x_offset - column_width, top]
            
            self.define_grid(columns=2, rows=body_row_count, gutter=0)
            
            # Header
            x, y, w, h = self.grid_box(0, 0, 1, 2)
            self.c.setFont(self.font_bold, 20)
            self.c.drawString(x, y + h - 20, date.strftime("%A"))
            
            x, y, w, h = self.grid_box(1, 0, 1, 2)
            self.c.setFont(self.font_name, 10)
            self.c.setFillColor(MEDIUM_COLOR)
            self.c.drawString(x, y + h - 12, date.strftime("%B %-d"))
            self.c.setFillColor(DARK_COLOR)
            
            task_start_row = header_row_count
            task_last_row = task_start_row + task_row_count - 1
            
            # Task label
            x, y, w, h = self.grid_box(task_start_row, 0, 1, 2)
            self.c.setFont(self.font_bold, 10)
            self.c.drawString(x + 6, y + h/2 - 3, "Tasks:")
            
            # Horizontal lines for tasks
            for row in range(task_start_row, task_last_row + 1):
                x, y, w, h = self.grid_box(row, 0, 1, 2)
                self.c.line(x, y, x + w, y)
            
            # Checkboxes
            checkbox_padding = 6
            checkbox_size = self.grid['row_height'] - (2 * checkbox_padding)
            for row in range(task_start_row + 1, task_last_row + 1):
                x, y, w, h = self.grid_box(row, 0)
                self.draw_checkbox(x, y + h - checkbox_size - 2*checkbox_padding, checkbox_size, checkbox_padding)
            
            # Hour Grid
            hour_start_row = task_last_row + 1
            hour_last_row = hour_start_row + hour_row_count - 1
            
            # Horizontal lines for hours
            for row in range(hour_start_row, hour_last_row + 1):
                x, y, w, h = self.grid_box(row, 0, 1, 2)
                self.c.line(x, y, x + w, y)
            
            # Vertical lines for hour grid
            overhang = 24
            x1, y1, w1, h1 = self.grid_box(hour_start_row + 1, 0, 1, 1)
            x2, y2, w2, h2 = self.grid_box(hour_last_row, 0, 1, 1)
            
            self.c.saveState()
            self.c.setDash([1, 2])
            self.c.line(x1 + overhang, y1 + h1, x2 + overhang, y2)
            self.c.line(x1 + w1 + overhang * 0.5, y1 + h1, x2 + w2 + overhang * 0.5, y2)
            
            x1, y1, w1, h1 = self.grid_box(hour_start_row + 1, 1, 1, 1)
            x2, y2, w2, h2 = self.grid_box(hour_last_row, 1, 1, 1)
            self.c.line(x1 + w1, y1 + h1, x2 + w2, y2)
            self.c.restoreState()
            
            # Hour labels
            for hour in range(HOUR_COUNT):
                if HOUR_LABELS[hour]:
                    x, y, w, h = self.grid_box(hour + hour_start_row + 1, 0)
                    self.c.setFont(self.font_name, 10)
                    self.c.drawRightString(x + 20, y + h/2 - 3, str(HOUR_LABELS[hour]))
            
            self.current_margins = old_margins
            self.c.restoreState()
    
    def save(self):
        """Save the PDF"""
        self.c.save()


def main():
    pdf = PlannerPDF(FILE_NAME)
    
    # Determine starting Sunday
    if len(sys.argv) > 1:
        date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
        print(f"Parsed {date} from arguments")
        sunday = date - timedelta(days=date.weekday() + 1 if date.weekday() != 6 else 0)
    else:
        date = datetime.now().date()
        if date.weekday() > 2:  # Wednesday or later
            print("Generating pages for the next week")
            sunday = date + timedelta(days=(6 - date.weekday()))
        else:
            print("Generating pages for this week")
            sunday = date - timedelta(days=(date.weekday() + 1 if date.weekday() != 6 else 0))
    
    for week in range(WEEKS):
        # Start a new page for the week ahead
        if week == 0:
            # First week - need to start the first page
            pdf.begin_new_page('right')
        else:
            # Subsequent weeks already have a page from previous iteration
            pdf.begin_new_page('right')
        
        monday = sunday + timedelta(days=1)
        friday = sunday + timedelta(days=5)
        print(f"Generate pages for week {monday.strftime('%W')}: {monday.strftime('%A, %B %-d, %Y')} "
              f"through {friday.strftime('%A, %B %-d, %Y')} in {FILE_NAME}")
        
        pdf.week_ahead_page(monday, friday)
        
        # Weekdays
        for i in range(1, 6):
            day = sunday + timedelta(days=i)
            pdf.daily_tasks_page(day)
            pdf.daily_calendar_page(day)
        
        # Weekend
        pdf.weekend_page(sunday + timedelta(days=6), sunday + timedelta(days=7))
        
        sunday = sunday + timedelta(days=7)
    
    pdf.save()
    print(f"PDF generated: {FILE_NAME}")


if __name__ == "__main__":
    main()
