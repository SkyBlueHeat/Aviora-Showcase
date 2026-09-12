import csv
import os

# Create Notion templates directory
os.makedirs('c:/Users/erkay/Desktop/önemli/notion_templates', exist_ok=True)

# Applications CSV for Notion
applications_data = [
    ['Company', 'Role', 'Location', 'Remote', 'Salary', 'Source', 'Date Applied', 'Status', 'Priority', 'Fit Score', 'Follow-up Date', 'Recruiter', 'Interview Date', 'Offer', 'Notes'],
    ['Tech Corp', 'Senior Frontend Developer', 'San Francisco, CA', 'Yes', '$150,000', 'LinkedIn', '2026-06-28', 'Applied', 'High', '85', '', 'John Doe', '', '', '']
]

with open('c:/Users/erkay/Desktop/önemli/notion_templates/applications.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(applications_data)

# Interview Tracker CSV
interview_data = [
    ['Company', 'Role', 'Interview Stage', 'Interviewer', 'Interview Date', 'Preparation Notes', 'Result', 'Rating', 'Lessons Learned'],
    ['Tech Corp', 'Senior Frontend Developer', 'Technical', 'Jane Smith', '', '', 'Pending', '', '']
]

with open('c:/Users/erkay/Desktop/önemli/notion_templates/interview_tracker.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(interview_data)

# Recruiter CRM CSV
recruiter_data = [
    ['Recruiter Name', 'Company', 'Email', 'LinkedIn', 'Position', 'Last Contact', 'Next Follow-up', 'Relationship Score', 'Notes'],
    ['John Doe', 'Tech Corp', 'john@techcorp.com', 'linkedin.com/in/johndoe', 'Technical Recruiter', '', '', '5', '']
]

with open('c:/Users/erkay/Desktop/önemli/notion_templates/recruiter_crm.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(recruiter_data)

# Target Companies CSV
target_data = [
    ['Company', 'Industry', 'Location', 'Remote', 'Size', 'Website', 'Status', 'Priority', 'Notes'],
    ['Tech Corp', 'Software', 'San Francisco, CA', 'Yes', '1000+', 'techcorp.com', 'Researching', 'High', '']
]

with open('c:/Users/erkay/Desktop/önemli/notion_templates/target_companies.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(target_data)

# Salary Comparison CSV
salary_data = [
    ['Company', 'Base Salary', 'Bonus', 'Equity', 'Benefits', 'PTO', 'Remote', 'Visa Sponsorship', 'Total Compensation', 'Decision Score'],
    ['Tech Corp', '150000', '20000', '50000', 'Full Health', '20 days', 'Yes', 'Yes', '220000', '']
]

with open('c:/Users/erkay/Desktop/önemli/notion_templates/salary_comparison.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(salary_data)

print("Notion CSV templates created successfully!")
