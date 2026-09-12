import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Load the workbook
wb = openpyxl.load_workbook('c:/Users/erkay/Desktop/önemli/Developer_Job_Application_Tracker_PRO.xlsx')

# Define styles
HEADER_FONT = Font(name="Segoe UI", size=12, bold=True, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="222222", end_color="222222", fill_type="solid")
BODY_FONT = Font(name="Segoe UI", size=10, color="222222")

# Create Portfolio Projects sheet
portfolio = wb.create_sheet("Portfolio Projects", 9)

# Column headers
portfolio_headers = [
    "Project Name", "Description", "Status", "Start Date", "Completion Date",
    "Type", "Tech Stack", "GitHub URL", "Live Demo", "Skills Demonstrated",
    "Complexity", "Time Investment", "Showcase Ready", "Interview Worthy", "Notes"
]

for i, header in enumerate(portfolio_headers):
    cell = portfolio.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    portfolio.column_dimensions[get_column_letter(i+1)].width = 18

# Add dropdown validation for Status
from openpyxl.worksheet.datavalidation import DataValidation
status_validation = DataValidation(type="list", formula1='"Idea,In Progress,Completed,On Hold,Archived"', allow_blank=True)
status_validation.range = "C2:C500"
portfolio.add_data_validation(status_validation)

# Add dropdown for Type
type_validation = DataValidation(type="list", formula1='"Web App,Mobile App,API,Library,Tool,Other"', allow_blank=True)
type_validation.range = "G2:G500"
portfolio.add_data_validation(type_validation)

# Add dropdown for Complexity
complexity_validation = DataValidation(type="list", formula1='"Beginner,Intermediate,Advanced,Expert"', allow_blank=True)
complexity_validation.range = "L2:L500"
portfolio.add_data_validation(complexity_validation)

# Add dropdown for Showcase Ready
showcase_validation = DataValidation(type="list", formula1='"Ready,Needs Work,Not Ready"', allow_blank=True)
showcase_validation.range = "N2:N500"
portfolio.add_data_validation(showcase_validation)

# Add dropdown for Interview Worthy
worthy_validation = DataValidation(type="list", formula1='"Yes,Needs Improvement,No"', allow_blank=True)
worthy_validation.range = "O2:O500"
portfolio.add_data_validation(worthy_validation)

# Sample data
sample_project = [
    "E-Commerce Platform", "Full-stack e-commerce solution", "Completed", "2026-01-15", "2026-03-30",
    "Web App", "React, Node.js, MongoDB, Stripe", "github.com/user/ecommerce", "demo.example.com",
    "Frontend, Backend, Database, API", "Advanced", "120 hours", "Ready", "Yes", ""
]

for i, value in enumerate(sample_project):
    portfolio.cell(row=2, column=i+1, value=value)
    portfolio.cell(row=2, column=i+1).font = BODY_FONT
    portfolio.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# Save workbook
wb.save('c:/Users/erkay/Desktop/önemli/Developer_Job_Application_Tracker_PRO.xlsx')
print("Portfolio Projects sheet added successfully!")
