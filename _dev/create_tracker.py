import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import PieChart, BarChart, Reference
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from datetime import datetime, timedelta

# Create workbook
wb = openpyxl.Workbook()

# Define brand colors
PRIMARY_FILL = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
SECONDARY_FILL = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
ACCENT_FILL = PatternFill(start_color="FF6B35", end_color="FF6B35", fill_type="solid")
SECONDARY_ACCENT_FILL = PatternFill(start_color="20C4B7", end_color="20C4B7", fill_type="solid")
HEADER_FILL = PatternFill(start_color="222222", end_color="222222", fill_type="solid")

# Define fonts
TITLE_FONT = Font(name="Segoe UI", size=24, bold=True, color="222222")
HEADER_FONT = Font(name="Segoe UI", size=12, bold=True, color="FFFFFF")
SUBHEADER_FONT = Font(name="Segoe UI", size=11, bold=True, color="222222")
BODY_FONT = Font(name="Segoe UI", size=10, color="222222")
ACCENT_FONT = Font(name="Segoe UI", size=14, bold=True, color="FF6B35")

# Define borders
THIN_BORDER = Border(
    left=Side(style='thin', color='DDDDDD'),
    right=Side(style='thin', color='DDDDDD'),
    top=Side(style='thin', color='DDDDDD'),
    bottom=Side(style='thin', color='DDDDDD')
)

# Remove default sheet
wb.remove(wb.active)

# ============================================
# DASHBOARD SHEET
# ============================================
dashboard = wb.create_sheet("Dashboard", 0)

# Set column widths
dashboard.column_dimensions['A'].width = 2
dashboard.column_dimensions['B'].width = 25
dashboard.column_dimensions['C'].width = 25
dashboard.column_dimensions['D'].width = 25
dashboard.column_dimensions['E'].width = 25
dashboard.column_dimensions['F'].width = 25
dashboard.column_dimensions['G'].width = 25

# Title
dashboard['B2'] = "Developer Job Application Tracker"
dashboard['B2'].font = TITLE_FONT
dashboard['B2'].alignment = Alignment(horizontal='left', vertical='center')
dashboard.merge_cells('B2:G2')

# KPI Cards Row 1
kpi_labels = ["Applications Sent", "Interviews", "Offers", "Rejections"]
kpi_cells = ['B5', 'D5', 'F5', 'H5']
kpi_value_cells = ['B6', 'D6', 'F6', 'H6']

for i, (label, cell, value_cell) in enumerate(zip(kpi_labels, kpi_cells, kpi_value_cells)):
    # Card background
    dashboard[cell] = label
    dashboard[cell].font = SUBHEADER_FONT
    dashboard[cell].fill = SECONDARY_FILL
    dashboard[cell].alignment = Alignment(horizontal='center', vertical='center')
    
    # Value cell
    dashboard[value_cell] = 0
    dashboard[value_cell].font = ACCENT_FONT
    dashboard[value_cell].alignment = Alignment(horizontal='center', vertical='center')
    dashboard[value_cell].fill = PRIMARY_FILL

# KPI Cards Row 2
kpi_labels_2 = ["Response Rate", "Interview Rate", "Offer Rate", "Ghosted"]
kpi_cells_2 = ['B9', 'D9', 'F9', 'H9']
kpi_value_cells_2 = ['B10', 'D10', 'F10', 'H10']

for i, (label, cell, value_cell) in enumerate(zip(kpi_labels_2, kpi_cells_2, kpi_value_cells_2)):
    dashboard[cell] = label
    dashboard[cell].font = SUBHEADER_FONT
    dashboard[cell].fill = SECONDARY_FILL
    dashboard[cell].alignment = Alignment(horizontal='center', vertical='center')
    
    dashboard[value_cell] = "0%"
    dashboard[value_cell].font = ACCENT_FONT
    dashboard[value_cell].alignment = Alignment(horizontal='center', vertical='center')
    dashboard[value_cell].fill = PRIMARY_FILL

# Salary KPIs
dashboard['B13'] = "Average Salary"
dashboard['B13'].font = SUBHEADER_FONT
dashboard['B13'].fill = SECONDARY_FILL
dashboard['B13'].alignment = Alignment(horizontal='center', vertical='center')
dashboard['B14'] = "$0"
dashboard['B14'].font = ACCENT_FONT
dashboard['B14'].alignment = Alignment(horizontal='center', vertical='center')

dashboard['D13'] = "Highest Offer"
dashboard['D13'].font = SUBHEADER_FONT
dashboard['D13'].fill = SECONDARY_FILL
dashboard['D13'].alignment = Alignment(horizontal='center', vertical='center')
dashboard['D14'] = "$0"
dashboard['D14'].font = ACCENT_FONT
dashboard['D14'].alignment = Alignment(horizontal='center', vertical='center')

dashboard['F13'] = "Applications This Week"
dashboard['F13'].font = SUBHEADER_FONT
dashboard['F13'].fill = SECONDARY_FILL
dashboard['F13'].alignment = Alignment(horizontal='center', vertical='center')
dashboard['F14'] = 0
dashboard['F14'].font = ACCENT_FONT
dashboard['F14'].alignment = Alignment(horizontal='center', vertical='center')

dashboard['H13'] = "Applications This Month"
dashboard['H13'].font = SUBHEADER_FONT
dashboard['H13'].fill = SECONDARY_FILL
dashboard['H13'].alignment = Alignment(horizontal='center', vertical='center')
dashboard['H14'] = 0
dashboard['H14'].font = ACCENT_FONT
dashboard['H14'].alignment = Alignment(horizontal='center', vertical='center')

# Section Headers
dashboard['B17'] = "Job Pipeline Status"
dashboard['B17'].font = SUBHEADER_FONT
dashboard['B17'].fill = SECONDARY_FILL
dashboard.merge_cells('B17:D17')

dashboard['F17'] = "Recent Activity"
dashboard['F17'].font = SUBHEADER_FONT
dashboard['F17'].fill = SECONDARY_FILL
dashboard.merge_cells('F17:G17')

# Pipeline table headers
pipeline_headers = ["Status", "Count", "Percentage"]
for i, header in enumerate(pipeline_headers):
    cell = dashboard.cell(row=18, column=2+i)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center')

# Pipeline data
pipeline_statuses = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Ghosted"]
for i, status in enumerate(pipeline_statuses):
    dashboard.cell(row=19+i, column=2, value=status)
    dashboard.cell(row=19+i, column=2).font = BODY_FONT
    dashboard.cell(row=19+i, column=2).alignment = Alignment(horizontal='left', vertical='center')
    dashboard.cell(row=19+i, column=3, value=0)
    dashboard.cell(row=19+i, column=3).font = BODY_FONT
    dashboard.cell(row=19+i, column=3).alignment = Alignment(horizontal='center', vertical='center')
    dashboard.cell(row=19+i, column=4, value="0%")
    dashboard.cell(row=19+i, column=4).font = BODY_FONT
    dashboard.cell(row=19+i, column=4).alignment = Alignment(horizontal='center', vertical='center')

# Recent Activity table
activity_headers = ["Company", "Status", "Date"]
for i, header in enumerate(activity_headers):
    cell = dashboard.cell(row=18, column=6+i)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center')

for i in range(5):
    for j in range(3):
        cell = dashboard.cell(row=19+i, column=6+j)
        cell.value = ""
        cell.font = BODY_FONT
        cell.alignment = Alignment(horizontal='left', vertical='center')

# Upcoming Follow-ups Section
dashboard['B27'] = "Upcoming Follow-ups"
dashboard['B27'].font = SUBHEADER_FONT
dashboard['B27'].fill = SECONDARY_FILL
dashboard.merge_cells('B27:D27')

followup_headers = ["Company", "Follow-up Date", "Priority"]
for i, header in enumerate(followup_headers):
    cell = dashboard.cell(row=28, column=2+i)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center')

for i in range(5):
    for j in range(3):
        cell = dashboard.cell(row=29+i, column=2+j)
        cell.value = ""
        cell.font = BODY_FONT
        cell.alignment = Alignment(horizontal='left', vertical='center')

# Priority Jobs Section
dashboard['F27'] = "Priority Jobs"
dashboard['F27'].font = SUBHEADER_FONT
dashboard['F27'].fill = SECONDARY_FILL
dashboard.merge_cells('F27:G27')

priority_headers = ["Company", "Role", "Fit Score"]
for i, header in enumerate(priority_headers):
    cell = dashboard.cell(row=28, column=6+i)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center')

for i in range(5):
    for j in range(3):
        cell = dashboard.cell(row=29+i, column=6+j)
        cell.value = ""
        cell.font = BODY_FONT
        cell.alignment = Alignment(horizontal='left', vertical='center')

# ============================================
# APPLICATIONS SHEET
# ============================================
applications = wb.create_sheet("Applications", 1)

# Column headers
app_headers = [
    "Company", "Role", "Location", "Remote", "Salary", "Source",
    "Date Applied", "Status", "Priority", "Fit Score", 
    "Follow-up Date", "Recruiter", "Interview Date", "Offer", "Notes"
]

for i, header in enumerate(app_headers):
    cell = applications.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    applications.column_dimensions[get_column_letter(i+1)].width = 18

# Add dropdown validation for Status
status_validation = DataValidation(type="list", formula1='"Applied,Screening,Interview,Offer,Rejected,Ghosted"', allow_blank=True)
status_validation.range = "H2:H500"
applications.add_data_validation(status_validation)

# Add dropdown validation for Priority
priority_validation = DataValidation(type="list", formula1='"High,Medium,Low"', allow_blank=True)
priority_validation.range = "I2:I500"
applications.add_data_validation(priority_validation)

# Add dropdown validation for Remote
remote_validation = DataValidation(type="list", formula1='"Yes,No,Hybrid"', allow_blank=True)
remote_validation.range = "D2:D500"
applications.add_data_validation(remote_validation)

# Add dropdown validation for Source
source_validation = DataValidation(type="list", formula1='"LinkedIn,Indeed,Company Site,Referral,Angel List,Other"', allow_blank=True)
source_validation.range = "F2:F500"
applications.add_data_validation(source_validation)

# Add sample data row
sample_row = [
    "Tech Corp", "Senior Frontend Developer", "San Francisco, CA", "Yes", 
    "$150,000", "LinkedIn", datetime.now().strftime("%Y-%m-%d"), "Applied", 
    "High", "85", "", "John Doe", "", "", ""
]
for i, value in enumerate(sample_row):
    applications.cell(row=2, column=i+1, value=value)
    applications.cell(row=2, column=i+1).font = BODY_FONT
    applications.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# INTERVIEW TRACKER SHEET
# ============================================
interview_tracker = wb.create_sheet("Interview Tracker", 2)

interview_headers = [
    "Company", "Role", "Interview Stage", "Interviewer", 
    "Interview Date", "Preparation Notes", "Result", "Rating", "Lessons Learned"
]

for i, header in enumerate(interview_headers):
    cell = interview_tracker.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    interview_tracker.column_dimensions[get_column_letter(i+1)].width = 20

# Dropdown for Interview Stage
stage_validation = DataValidation(type="list", formula1='"Recruiter Screen,Technical,Live Coding,System Design,HR,Final,Offer,Rejected"', allow_blank=True)
stage_validation.range = "C2:C500"
interview_tracker.add_data_validation(stage_validation)

# Dropdown for Result
result_validation = DataValidation(type="list", formula1='"Pending,Passed,Rejected"', allow_blank=True)
result_validation.range = "G2:G500"
interview_tracker.add_data_validation(result_validation)

# Dropdown for Rating
rating_validation = DataValidation(type="list", formula1='"1,2,3,4,5"', allow_blank=True)
rating_validation.range = "H2:H500"
interview_tracker.add_data_validation(rating_validation)

# Sample data
interview_sample = [
    "Tech Corp", "Senior Frontend Developer", "Technical", "Jane Smith",
    "", "", "Pending", "", ""
]
for i, value in enumerate(interview_sample):
    interview_tracker.cell(row=2, column=i+1, value=value)
    interview_tracker.cell(row=2, column=i+1).font = BODY_FONT
    interview_tracker.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# RECRUITER CRM SHEET
# ============================================
recruiter_crm = wb.create_sheet("Recruiter CRM", 3)

crm_headers = [
    "Recruiter Name", "Company", "Email", "LinkedIn", "Position",
    "Last Contact", "Next Follow-up", "Relationship Score", "Notes"
]

for i, header in enumerate(crm_headers):
    cell = recruiter_crm.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    recruiter_crm.column_dimensions[get_column_letter(i+1)].width = 18

# Dropdown for Relationship Score
score_validation = DataValidation(type="list", formula1='"1,2,3,4,5"', allow_blank=True)
score_validation.range = "H2:H500"
recruiter_crm.add_data_validation(score_validation)

# Sample data
crm_sample = [
    "John Doe", "Tech Corp", "john@techcorp.com", "linkedin.com/in/johndoe", 
    "Technical Recruiter", "", "", "5", ""
]
for i, value in enumerate(crm_sample):
    recruiter_crm.cell(row=2, column=i+1, value=value)
    recruiter_crm.cell(row=2, column=i+1).font = BODY_FONT
    recruiter_crm.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# TARGET COMPANIES SHEET
# ============================================
target_companies = wb.create_sheet("Target Companies", 4)

target_headers = [
    "Company", "Industry", "Location", "Remote", "Size", 
    "Website", "Status", "Priority", "Notes"
]

for i, header in enumerate(target_headers):
    cell = target_companies.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    target_companies.column_dimensions[get_column_letter(i+1)].width = 16

# Dropdown for Status
target_status_validation = DataValidation(type="list", formula1='"Researching,Applied,Interviewing,Offer,Rejected,Not Interested"', allow_blank=True)
target_status_validation.range = "G2:G500"
target_companies.add_data_validation(target_status_validation)

# Dropdown for Priority
target_priority_validation = DataValidation(type="list", formula1='"High,Medium,Low"', allow_blank=True)
target_priority_validation.range = "H2:H500"
target_companies.add_data_validation(target_priority_validation)

# Sample data
target_sample = [
    "Tech Corp", "Software", "San Francisco, CA", "Yes", "1000+",
    "techcorp.com", "Researching", "High", ""
]
for i, value in enumerate(target_sample):
    target_companies.cell(row=2, column=i+1, value=value)
    target_companies.cell(row=2, column=i+1).font = BODY_FONT
    target_companies.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# SALARY COMPARISON SHEET
# ============================================
salary_comparison = wb.create_sheet("Salary Comparison", 5)

salary_headers = [
    "Company", "Base Salary", "Bonus", "Equity", "Benefits",
    "PTO", "Remote", "Visa Sponsorship", "Total Compensation", "Decision Score"
]

for i, header in enumerate(salary_headers):
    cell = salary_comparison.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    salary_comparison.column_dimensions[get_column_letter(i+1)].width = 16

# Dropdown for Remote
salary_remote_validation = DataValidation(type="list", formula1='"Yes,No,Hybrid"', allow_blank=True)
salary_remote_validation.range = "G2:G500"
salary_comparison.add_data_validation(salary_remote_validation)

# Dropdown for Visa Sponsorship
visa_validation = DataValidation(type="list", formula1='"Yes,No,Maybe"', allow_blank=True)
visa_validation.range = "H2:H500"
salary_comparison.add_data_validation(visa_validation)

# Sample data with formula for Total Compensation
salary_sample = [
    "Tech Corp", 150000, 20000, 50000, "Full Health", "20 days", 
    "Yes", "Yes", "=B2+C2+D2", ""
]
for i, value in enumerate(salary_sample):
    salary_comparison.cell(row=2, column=i+1, value=value)
    salary_comparison.cell(row=2, column=i+1).font = BODY_FONT
    salary_comparison.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# WEEKLY PLANNER SHEET
# ============================================
weekly_planner = wb.create_sheet("Weekly Planner", 6)

weekly_headers = [
    "Week Of", "Applications Goal", "Completed", "Networking", 
    "Interview Prep", "Learning", "Follow-ups", "Reflection"
]

for i, header in enumerate(weekly_headers):
    cell = weekly_planner.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    weekly_planner.column_dimensions[get_column_letter(i+1)].width = 18

# Sample data
weekly_sample = [
    datetime.now().strftime("%Y-%m-%d"), 20, 0, "3 coffee chats", 
    "2 companies", "React patterns", "5 follow-ups", ""
]
for i, value in enumerate(weekly_sample):
    weekly_planner.cell(row=2, column=i+1, value=value)
    weekly_planner.cell(row=2, column=i+1).font = BODY_FONT
    weekly_planner.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# JOB SEARCH STATISTICS SHEET
# ============================================
statistics = wb.create_sheet("Statistics", 7)

# Title
statistics['B2'] = "Job Search Statistics"
statistics['B2'].font = TITLE_FONT
statistics.merge_cells('B2:G2')

# Statistics table
stats_headers = ["Metric", "Value", "Target", "Progress"]
for i, header in enumerate(stats_headers):
    cell = statistics.cell(row=4, column=2+i)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center')

stats_metrics = [
    ["Total Applications", "0", "50", "0%"],
    ["Total Interviews", "0", "10", "0%"],
    ["Total Offers", "0", "3", "0%"],
    ["Networking Contacts", "0", "20", "0%"],
    ["Companies Researched", "0", "30", "0%"],
    ["Applications/Week", "0", "15", "0%"]
]

for i, metric in enumerate(stats_metrics):
    for j, value in enumerate(metric):
        cell = statistics.cell(row=5+i, column=2+j)
        cell.value = value
        cell.font = BODY_FONT
        cell.alignment = Alignment(horizontal='center', vertical='center')

# ============================================
# NOTES SHEET
# ============================================
notes = wb.create_sheet("Notes", 8)

notes['B2'] = "Notes"
notes['B2'].font = TITLE_FONT
notes.merge_cells('B2:G2')

notes['B4'] = "General Notes"
notes['B4'].font = SUBHEADER_FONT
notes['B4'].fill = SECONDARY_FILL

notes['B5'] = ""
notes['B5'].alignment = Alignment(wrap_text=True)

# ============================================
# NETWORKING TRACKER SHEET
# ============================================
networking = wb.create_sheet("Networking Tracker", 9)

networking_headers = [
    "Contact Name", "Company", "LinkedIn", "Email", "Connection Date",
    "Relationship Type", "Last Contact", "Next Follow-up", "Network Score",
    "Referral Status", "Notes", "Coffee Chat Scheduled", "Event Met"
]

for i, header in enumerate(networking_headers):
    cell = networking.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    networking.column_dimensions[get_column_letter(i+1)].width = 16

# Dropdown for Relationship Type
rel_type_validation = DataValidation(type="list", formula1='"LinkedIn Connection,Alumni,Former Colleague,Conference Meetup,Referral,Cold Contact"', allow_blank=True)
rel_type_validation.range = "F2:F500"
networking.add_data_validation(rel_type_validation)

# Dropdown for Network Score
network_score_validation = DataValidation(type="list", formula1='"1,2,3,4,5,6,7,8,9,10"', allow_blank=True)
network_score_validation.range = "I2:I500"
networking.add_data_validation(network_score_validation)

# Dropdown for Referral Status
referral_validation = DataValidation(type="list", formula1='"Not Asked,Asked - Pending,Referral Given,Referral Denied,N/A"', allow_blank=True)
referral_validation.range = "J2:J500"
networking.add_data_validation(referral_validation)

# Sample data
networking_sample = [
    "Jane Smith", "Google", "linkedin.com/in/janesmith", "jane@google.com",
    datetime.now().strftime("%Y-%m-%d"), "LinkedIn Connection", "", "", "8",
    "Not Asked", "", "No", "No"
]
for i, value in enumerate(networking_sample):
    networking.cell(row=2, column=i+1, value=value)
    networking.cell(row=2, column=i+1).font = BODY_FONT
    networking.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# SKILL GAP ANALYSIS SHEET
# ============================================
skill_gap = wb.create_sheet("Skill Gap Analysis", 10)

skill_headers = [
    "Skill Category", "Skill Name", "Current Level", "Target Level", "Gap",
    "Learning Resource", "Priority", "Status", "Start Date", "Target Date",
    "Progress %", "Hours Invested", "Notes"
]

for i, header in enumerate(skill_headers):
    cell = skill_gap.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    skill_gap.column_dimensions[get_column_letter(i+1)].width = 14

# Dropdown for Current Level
current_level_validation = DataValidation(type="list", formula1='"None,Beginner,Intermediate,Advanced,Expert"', allow_blank=True)
current_level_validation.range = "C2:C500"
skill_gap.add_data_validation(current_level_validation)

# Dropdown for Target Level
target_level_validation = DataValidation(type="list", formula1='"Beginner,Intermediate,Advanced,Expert"', allow_blank=True)
target_level_validation.range = "D2:D500"
skill_gap.add_data_validation(target_level_validation)

# Dropdown for Priority
skill_priority_validation = DataValidation(type="list", formula1='"Critical,High,Medium,Low"', allow_blank=True)
skill_priority_validation.range = "G2:G500"
skill_gap.add_data_validation(skill_priority_validation)

# Dropdown for Status
skill_status_validation = DataValidation(type="list", formula1='"Not Started,In Progress,Completed,On Hold"', allow_blank=True)
skill_status_validation.range = "H2:H500"
skill_gap.add_data_validation(skill_status_validation)

# Sample data
skill_sample = [
    "Frontend", "React", "Intermediate", "Advanced", "1 level",
    "React Official Docs", "High", "Not Started", "", "", "0%", "0", ""
]
for i, value in enumerate(skill_sample):
    skill_gap.cell(row=2, column=i+1, value=value)
    skill_gap.cell(row=2, column=i+1).font = BODY_FONT
    skill_gap.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# COVER LETTER TRACKER SHEET
# ============================================
cover_letter = wb.create_sheet("Cover Letter Tracker", 11)

cover_headers = [
    "Company", "Role", "Version", "Date Created", "Date Sent",
    "Template Used", "Customization Level", "Response Received", "Interview Scheduled",
    "Success Rate", "A/B Test Group", "Notes"
]

for i, header in enumerate(cover_headers):
    cell = cover_letter.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    cover_letter.column_dimensions[get_column_letter(i+1)].width = 16

# Dropdown for Customization Level
custom_level_validation = DataValidation(type="list", formula1='"Template Only,Light Customization,Heavy Customization,From Scratch"', allow_blank=True)
custom_level_validation.range = "G2:G500"
cover_letter.add_data_validation(custom_level_validation)

# Dropdown for Response Received
response_validation = DataValidation(type="list", formula1='"Yes,No,Pending"', allow_blank=True)
response_validation.range = "H2:H500"
cover_letter.add_data_validation(response_validation)

# Dropdown for Interview Scheduled
interview_sched_validation = DataValidation(type="list", formula1='"Yes,No,Pending"', allow_blank=True)
interview_sched_validation.range = "I2:I500"
cover_letter.add_data_validation(interview_sched_validation)

# Dropdown for A/B Test Group
ab_test_validation = DataValidation(type="list", formula1='"A,B,Control"', allow_blank=True)
ab_test_validation.range = "K2:K500"
cover_letter.add_data_validation(ab_test_validation)

# Sample data
cover_sample = [
    "Tech Corp", "Senior Frontend Developer", "v1.0", datetime.now().strftime("%Y-%m-%d"),
    "", "Template A", "Heavy Customization", "No", "No", "0%", "A", ""
]
for i, value in enumerate(cover_sample):
    cover_letter.cell(row=2, column=i+1, value=value)
    cover_letter.cell(row=2, column=i+1).font = BODY_FONT
    cover_letter.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# JOB SEARCH CALENDAR SHEET
# ============================================
job_calendar = wb.create_sheet("Job Search Calendar", 12)

calendar_headers = [
    "Date", "Event Type", "Company", "Role", "Time",
    "Location/Link", "Preparation Needed", "Status", "Priority",
    "Follow-up Required", "Notes"
]

for i, header in enumerate(calendar_headers):
    cell = job_calendar.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    job_calendar.column_dimensions[get_column_letter(i+1)].width = 15

# Dropdown for Event Type
event_type_validation = DataValidation(type="list", formula1='"Interview,Phone Screen,Technical Assessment,On-site,Networking Event,Coffee Chat,Application Deadline,Follow-up Call"', allow_blank=True)
event_type_validation.range = "B2:B500"
job_calendar.add_data_validation(event_type_validation)

# Dropdown for Status
calendar_status_validation = DataValidation(type="list", formula1='"Scheduled,Completed,Cancelled,Rescheduled,Missed"', allow_blank=True)
calendar_status_validation.range = "H2:H500"
job_calendar.add_data_validation(calendar_status_validation)

# Dropdown for Priority
calendar_priority_validation = DataValidation(type="list", formula1='"High,Medium,Low"', allow_blank=True)
calendar_priority_validation.range = "I2:I500"
job_calendar.add_data_validation(calendar_priority_validation)

# Sample data
calendar_sample = [
    datetime.now().strftime("%Y-%m-%d"), "Technical Assessment", "Tech Corp",
    "Senior Frontend Developer", "2:00 PM", "Online (Zoom)", "Practice coding problems",
    "Scheduled", "High", "Yes", ""
]
for i, value in enumerate(calendar_sample):
    job_calendar.cell(row=2, column=i+1, value=value)
    job_calendar.cell(row=2, column=i+1).font = BODY_FONT
    job_calendar.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# LEARNING RESOURCES SHEET
# ============================================
learning = wb.create_sheet("Learning Resources", 13)

learning_headers = [
    "Resource Name", "Type", "Provider", "Topic", "URL",
    "Cost", "Duration", "Start Date", "Completion Date", "Progress %",
    "Certificate", "Priority", "Rating", "Notes"
]

for i, header in enumerate(learning_headers):
    cell = learning.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    learning.column_dimensions[get_column_letter(i+1)].width = 14

# Dropdown for Type
resource_type_validation = DataValidation(type="list", formula1='"Course,Book,Video,Article,Podcast,Workshop,Certification,Bootcamp"', allow_blank=True)
resource_type_validation.range = "B2:B500"
learning.add_data_validation(resource_type_validation)

# Dropdown for Priority
learning_priority_validation = DataValidation(type="list", formula1='"Critical,High,Medium,Low"', allow_blank=True)
learning_priority_validation.range = "M2:M500"
learning.add_data_validation(learning_priority_validation)

# Dropdown for Rating
rating_validation = DataValidation(type="list", formula1='"1,2,3,4,5"', allow_blank=True)
rating_validation.range = "N2:N500"
learning.add_data_validation(rating_validation)

# Sample data
learning_sample = [
    "React - The Complete Guide", "Course", "Udemy", "React", "udemy.com/course/react",
    "$15", "40 hours", "", "", "0%", "Yes", "High", "", ""
]
for i, value in enumerate(learning_sample):
    learning.cell(row=2, column=i+1, value=value)
    learning.cell(row=2, column=i+1).font = BODY_FONT
    learning.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# OFFER DECISION MATRIX SHEET
# ============================================
offer_matrix = wb.create_sheet("Offer Decision Matrix", 14)

offer_headers = [
    "Company", "Base Salary", "Bonus", "Equity", "Benefits Value",
    "Remote", "PTO Days", "Work-Life Balance", "Career Growth", "Company Culture",
    "Team Quality", "Tech Stack", "Location", "Commute Time", "Visa Sponsorship",
    "Job Security", "Brand Recognition", "Learning Opportunities", "Total Score", "Decision"
]

for i, header in enumerate(offer_headers):
    cell = offer_matrix.cell(row=1, column=i+1)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    offer_matrix.column_dimensions[get_column_letter(i+1)].width = 14

# Dropdown for Remote
offer_remote_validation = DataValidation(type="list", formula1='"Yes,No,Hybrid"', allow_blank=True)
offer_remote_validation.range = "F2:F500"
offer_matrix.add_data_validation(offer_remote_validation)

# Dropdown for Visa Sponsorship
offer_visa_validation = DataValidation(type="list", formula1='"Yes,No,Maybe"', allow_blank=True)
offer_visa_validation.range = "O2:O500"
offer_matrix.add_data_validation(offer_visa_validation)

# Dropdown for Decision
decision_validation = DataValidation(type="list", formula1='"Pending,Accept,Decline,Negotiating"', allow_blank=True)
decision_validation.range = "T2:T500"
offer_matrix.add_data_validation(decision_validation)

# Sample data with formula for Total Score
offer_sample = [
    "Tech Corp", 150000, 20000, 50000, 15000, "Yes", 20, "8", "9", "8",
    "9", "9", "San Francisco", "30 min", "Yes", "8", "9", "9", "=AVERAGE(B2:S2)", "Pending"
]
for i, value in enumerate(offer_sample):
    offer_matrix.cell(row=2, column=i+1, value=value)
    offer_matrix.cell(row=2, column=i+1).font = BODY_FONT
    offer_matrix.cell(row=2, column=i+1).alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

# ============================================
# Save workbook
# ============================================
wb.save('c:/Users/erkay/Desktop/önemli/Developer_Job_Application_Tracker_PRO.xlsx')
print("Excel file created successfully with 16 sheets!")
