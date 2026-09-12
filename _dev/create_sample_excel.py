import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

# Create sample workbook
wb = openpyxl.Workbook()

# Dashboard sheet
dashboard = wb.active
dashboard.title = "Dashboard"
dashboard['A1'] = "PREVIEW VERSION - Purchase full version for complete functionality"
dashboard['A1'].font = Font(color="FF0000", bold=True)
dashboard['A3'] = "Applications Sent"
dashboard['A4'] = "Interviews"
dashboard['A5'] = "Offers"
dashboard['B3'] = "0"
dashboard['B4'] = "0"
dashboard['B5'] = "0"

# Applications sheet
apps = wb.create_sheet("Applications")
apps['A1'] = "PREVIEW - Sample Data Only"
apps['A2'] = "Company"
apps['B2'] = "Role"
apps['C2'] = "Location"
apps['D2'] = "Status"
apps['A3'] = "Tech Corp"
apps['B3'] = "Senior Developer"
apps['C3'] = "San Francisco"
apps['D3'] = "Applied"

# Interview Tracker sheet
interview = wb.create_sheet("Interview Tracker")
interview['A1'] = "PREVIEW - Sample Data Only"
interview['A2'] = "Company"
interview['B2'] = "Stage"
interview['C2'] = "Date"
interview['A3'] = "Tech Corp"
interview['B3'] = "Technical"
interview['C3'] = "2026-07-01"

# Save
wb.save('c:/Users/erkay/Desktop/önemli/SAMPLE_Excel_Preview.xlsx')
print("Sample Excel preview created!")
