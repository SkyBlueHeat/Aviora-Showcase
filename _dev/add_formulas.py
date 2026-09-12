import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

# Load the existing workbook
wb = openpyxl.load_workbook('c:/Users/erkay/Desktop/önemli/Developer_Job_Application_Tracker_PRO.xlsx')

dashboard = wb['Dashboard']
applications = wb['Applications']

# Define fonts
ACCENT_FONT = Font(name="Segoe UI", size=14, bold=True, color="FF6B35")
BODY_FONT = Font(name="Segoe UI", size=10, color="222222")

# ============================================
# DASHBOARD FORMULAS
# ============================================

# Applications Sent - Count all non-empty rows in Applications sheet
dashboard['B6'] = '=COUNTA(Applications!A:A)-1'
dashboard['B6'].font = ACCENT_FONT
dashboard['B6'].alignment = Alignment(horizontal='center', vertical='center')

# Interviews - Count applications with status "Interview"
dashboard['D6'] = '=COUNTIF(Applications!H:H,"Interview")'
dashboard['D6'].font = ACCENT_FONT
dashboard['D6'].alignment = Alignment(horizontal='center', vertical='center')

# Offers - Count applications with status "Offer"
dashboard['F6'] = '=COUNTIF(Applications!H:H,"Offer")'
dashboard['F6'].font = ACCENT_FONT
dashboard['F6'].alignment = Alignment(horizontal='center', vertical='center')

# Rejections - Count applications with status "Rejected"
dashboard['H6'] = '=COUNTIF(Applications!H:H,"Rejected")'
dashboard['H6'].font = ACCENT_FONT
dashboard['H6'].alignment = Alignment(horizontal='center', vertical='center')

# Response Rate - (Interviews + Offers + Rejections) / Applications Sent
dashboard['B10'] = '=IF(B6=0,0,(D6+F6+H6)/B6)'
dashboard['B10'].number_format = '0%'
dashboard['B10'].font = ACCENT_FONT
dashboard['B10'].alignment = Alignment(horizontal='center', vertical='center')

# Interview Rate - Interviews / Applications Sent
dashboard['D10'] = '=IF(B6=0,0,D6/B6)'
dashboard['D10'].number_format = '0%'
dashboard['D10'].font = ACCENT_FONT
dashboard['D10'].alignment = Alignment(horizontal='center', vertical='center')

# Offer Rate - Offers / Applications Sent
dashboard['F10'] = '=IF(B6=0,0,F6/B6)'
dashboard['F10'].number_format = '0%'
dashboard['F10'].font = ACCENT_FONT
dashboard['F10'].alignment = Alignment(horizontal='center', vertical='center')

# Ghosted - Count applications with status "Ghosted"
dashboard['H10'] = '=COUNTIF(Applications!H:H,"Ghosted")'
dashboard['H10'].font = ACCENT_FONT
dashboard['H10'].alignment = Alignment(horizontal='center', vertical='center')

# Average Salary - Average of salary column (column E)
dashboard['B14'] = '=AVERAGEIF(Applications!E:E,">*0",Applications!E:E)'
dashboard['B14'].number_format = '$#,##0'
dashboard['B14'].font = ACCENT_FONT
dashboard['B14'].alignment = Alignment(horizontal='center', vertical='center')

# Highest Offer - Max of salary column
dashboard['D14'] = '=MAX(Applications!E:E)'
dashboard['D14'].number_format = '$#,##0'
dashboard['D14'].font = ACCENT_FONT
dashboard['D14'].alignment = Alignment(horizontal='center', vertical='center')

# Applications This Week - Count applications from last 7 days
dashboard['F14'] = '=COUNTIFS(Applications!G:H,">="&TODAY()-7,Applications!G:H,"<="&TODAY())'
dashboard['F14'].font = ACCENT_FONT
dashboard['F14'].alignment = Alignment(horizontal='center', vertical='center')

# Applications This Month - Count applications from this month
dashboard['H14'] = '=COUNTIFS(Applications!G:H,">="&EOMONTH(TODAY(),-1)+1,Applications!G:H,"<="&EOMONTH(TODAY(),0))'
dashboard['H14'].font = ACCENT_FONT
dashboard['H14'].alignment = Alignment(horizontal='center', vertical='center')

# ============================================
# PIPELINE TABLE FORMULAS
# ============================================

pipeline_statuses = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Ghosted"]
for i, status in enumerate(pipeline_statuses):
    row = 19 + i
    # Count
    dashboard.cell(row=row, column=3, value=f'=COUNTIF(Applications!H:H,"{status}")')
    dashboard.cell(row=row, column=3).font = BODY_FONT
    dashboard.cell(row=row, column=3).alignment = Alignment(horizontal='center', vertical='center')
    
    # Percentage
    dashboard.cell(row=row, column=4, value=f'=IF($B$6=0,0,C{row}/$B$6)')
    dashboard.cell(row=row, column=4).number_format = '0%'
    dashboard.cell(row=row, column=4).font = BODY_FONT
    dashboard.cell(row=row, column=4).alignment = Alignment(horizontal='center', vertical='center')

# ============================================
# RECENT ACTIVITY FORMULAS
# ============================================

# Recent Activity - Last 5 applications by date
dashboard['F19'] = '=INDEX(Applications!A:A,MATCH(MAX(Applications!G:G),Applications!G:G,0))'
dashboard['G19'] = '=VLOOKUP(F19,Applications!A:H,8,FALSE)'
dashboard['H19'] = '=VLOOKUP(F19,Applications!A:G,7,FALSE)'

dashboard['F20'] = '=INDEX(Applications!A:A,LARGE(Applications!G:G,2))'
dashboard['G20'] = '=VLOOKUP(F20,Applications!A:H,8,FALSE)'
dashboard['H20'] = '=VLOOKUP(F20,Applications!A:G,7,FALSE)'

dashboard['F21'] = '=INDEX(Applications!A:A,LARGE(Applications!G:G,3))'
dashboard['G21'] = '=VLOOKUP(F21,Applications!A:H,8,FALSE)'
dashboard['H21'] = '=VLOOKUP(F21,Applications!A:G,7,FALSE)'

dashboard['F22'] = '=INDEX(Applications!A:A,LARGE(Applications!G:G,4))'
dashboard['G22'] = '=VLOOKUP(F22,Applications!A:H,8,FALSE)'
dashboard['H22'] = '=VLOOKUP(F22,Applications!A:G,7,FALSE)'

dashboard['F23'] = '=INDEX(Applications!A:A,LARGE(Applications!G:G,5))'
dashboard['G23'] = '=VLOOKUP(F23,Applications!A:H,8,FALSE)'
dashboard['H23'] = '=VLOOKUP(F23,Applications!A:G,7,FALSE)'

# Format recent activity cells
for row in range(19, 24):
    for col in range(6, 9):
        cell = dashboard.cell(row=row, column=col)
        cell.font = BODY_FONT
        cell.alignment = Alignment(horizontal='left', vertical='center')

# ============================================
# UPCOMING FOLLOW-UPS FORMULAS
# ============================================

# Upcoming Follow-ups - Next 5 follow-up dates
dashboard['B29'] = '=INDEX(Applications!A:A,MATCH(SMALL(Applications!K:K,COUNTIF(Applications!K:K,"")+1),Applications!K:K,0))'
dashboard['C29'] = '=VLOOKUP(B29,Applications!A:K,11,FALSE)'
dashboard['D29'] = '=VLOOKUP(B29,Applications!A:I,9,FALSE)'

dashboard['B30'] = '=INDEX(Applications!A:A,MATCH(SMALL(Applications!K:K,COUNTIF(Applications!K:K,"")+2),Applications!K:K,0))'
dashboard['C30'] = '=VLOOKUP(B30,Applications!A:K,11,FALSE)'
dashboard['D30'] = '=VLOOKUP(B30,Applications!A:I,9,FALSE)'

dashboard['B31'] = '=INDEX(Applications!A:A,MATCH(SMALL(Applications!K:K,COUNTIF(Applications!K:K,"")+3),Applications!K:K,0))'
dashboard['C31'] = '=VLOOKUP(B31,Applications!A:K,11,FALSE)'
dashboard['D31'] = '=VLOOKUP(B31,Applications!A:I,9,FALSE)'

# Format follow-up cells
for row in range(29, 32):
    for col in range(2, 5):
        cell = dashboard.cell(row=row, column=col)
        cell.font = BODY_FONT
        cell.alignment = Alignment(horizontal='left', vertical='center')

# ============================================
# PRIORITY JOBS FORMULAS
# ============================================

# Priority Jobs - Top 5 by Fit Score
dashboard['F29'] = '=INDEX(Applications!A:A,MATCH(LARGE(Applications!J:J,1),Applications!J:J,0))'
dashboard['G29'] = '=VLOOKUP(F29,Applications!A:B,2,FALSE)'
dashboard['H29'] = '=VLOOKUP(F29,Applications!A:J,10,FALSE)'

dashboard['F30'] = '=INDEX(Applications!A:A,MATCH(LARGE(Applications!J:J,2),Applications!J:J,0))'
dashboard['G30'] = '=VLOOKUP(F30,Applications!A:B,2,FALSE)'
dashboard['H30'] = '=VLOOKUP(F30,Applications!A:J,10,FALSE)'

dashboard['F31'] = '=INDEX(Applications!A:A,MATCH(LARGE(Applications!J:J,3),Applications!J:J,0))'
dashboard['G31'] = '=VLOOKUP(F31,Applications!A:B,2,FALSE)'
dashboard['H31'] = '=VLOOKUP(F31,Applications!A:J,10,FALSE)'

# Format priority jobs cells
for row in range(29, 32):
    for col in range(6, 9):
        cell = dashboard.cell(row=row, column=col)
        cell.font = BODY_FONT
        cell.alignment = Alignment(horizontal='left', vertical='center')

# ============================================
# Save workbook
# ============================================
wb.save('c:/Users/erkay/Desktop/önemli/Developer_Job_Application_Tracker_PRO.xlsx')
print("Formulas added successfully!")
