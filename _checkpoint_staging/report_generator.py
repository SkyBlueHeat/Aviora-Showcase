import openpyxl
from datetime import date, datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

# Report Generator Script
# Generates weekly and monthly job search reports

def _normalize_date(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%d/%m/%Y'):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                pass
    return None


def _get_weekly_goal(default=15):
    try:
        import settings
        return int(settings.get_weekly_goal())
    except Exception:
        return default


def _collect_recent_applications(ws, limit=10):
    items = []
    for row in range(2, ws.max_row + 1):
        # v3.0: Company=col2, Role=col3, Status=col10, DateApplied=col9
        company = ws.cell(row=row, column=2).value
        role = ws.cell(row=row, column=3).value
        status = ws.cell(row=row, column=10).value
        applied_at = _normalize_date(ws.cell(row=row, column=9).value)
        if not company and not role:
            continue
        sort_date = applied_at or datetime.min
        items.append((sort_date, row, company, role, status, applied_at))
    items.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return items[:limit]

def generate_weekly_report(file_path, output_path):
    """Generate a comprehensive weekly report"""
    wb = openpyxl.load_workbook(file_path)
    applications = wb['Applications']
    interviews = wb['Interview Tracker']
    
    # Calculate metrics
    total_apps = 0
    new_apps_this_week = 0
    interviews_this_week = 0
    offers_this_week = 0
    
    one_week_ago = datetime.now() - timedelta(days=7)
    weekly_goal = _get_weekly_goal(15)
    
    for row in range(2, applications.max_row + 1):
        # v3.0: DateApplied=col9, Status=col10
        date = _normalize_date(applications.cell(row=row, column=9).value)
        status = applications.cell(row=row, column=10).value
        
        if date:
            total_apps += 1
            if date >= one_week_ago:
                new_apps_this_week += 1
            if str(status or '').strip().lower() == 'offer' and date >= one_week_ago:
                offers_this_week += 1
    
    for row in range(2, interviews.max_row + 1):
        date = _normalize_date(interviews.cell(row=row, column=5).value)
        if date and date >= one_week_ago:
            interviews_this_week += 1
    
    # Generate report
    report = f"""
================================================================================
                    WEEKLY JOB SEARCH REPORT
================================================================================
Report Date: {datetime.now().strftime('%Y-%m-%d')}
Period: Last 7 Days

================================================================================
KEY METRICS
================================================================================
• Total Applications: {total_apps}
• New Applications This Week: {new_apps_this_week}
• Interviews Scheduled This Week: {interviews_this_week}
• Offers Received This Week: {offers_this_week}

================================================================================
APPLICATION ACTIVITY
================================================================================
"""
    
    # Add recent applications
    report += "\nRecent Applications:\n"
    for row in range(2, min(12, applications.max_row + 1)):
        # v3.0: Company=col2, Role=col3, Status=col10, DateApplied=col9
        company = applications.cell(row=row, column=2).value
        role = applications.cell(row=row, column=3).value
        status = applications.cell(row=row, column=10).value
        date = _normalize_date(applications.cell(row=row, column=9).value)
        
        if company:
            date_str = date.strftime('%Y-%m-%d') if date else 'N/A'
            report += f"• {company} - {role} | Status: {status} | Applied: {date_str}\n"
    
    report += """
================================================================================
UPCOMING FOLLOW-UPS
================================================================================
"""
    
    # Add upcoming follow-ups
    report += "\nFollow-ups needed in next 7 days:\n"
    followup_count = 0
    for row in range(2, applications.max_row + 1):
        # v3.0: Company=col2, FollowupDate=col13
        company = applications.cell(row=row, column=2).value
        followup_date = _normalize_date(applications.cell(row=row, column=13).value)
        
        if followup_date:
            days_until = (followup_date.date() - datetime.now().date()).days
            if 0 <= days_until <= 7:
                followup_count += 1
                report += f"• {company} - Follow-up due in {days_until} days ({followup_date.strftime('%Y-%m-%d')})\n"
    
    if followup_count == 0:
        report += "No follow-ups needed in the next 7 days.\n"
    
    report += """
================================================================================
WEEKLY GOALS & PROGRESS
================================================================================
• Application Goal: {}/week
• Progress: {}/{} ({:.0f}%)
• Networking Goal: 5 contacts/week
• Learning Goal: 10 hours/week

================================================================================
RECOMMENDATIONS
================================================================================
• Keep up the momentum! Your application rate is strong.
• Focus on companies with high fit scores.
• Schedule at least 3 networking coffee chats this week.
• Review and practice technical interview questions daily.

================================================================================
CreatorDockStudio - Your Job Search Success Partner
================================================================================
""".format(weekly_goal, new_apps_this_week, weekly_goal, (new_apps_this_week/weekly_goal)*100 if weekly_goal else 0)
    
    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Weekly report generated: {output_path}")
    return report

def generate_monthly_report(file_path, output_path):
    """Generate a comprehensive monthly report"""
    wb = openpyxl.load_workbook(file_path)
    applications = wb['Applications']
    
    # Calculate monthly metrics
    one_month_ago = datetime.now() - timedelta(days=30)
    
    monthly_apps = 0
    monthly_interviews = 0
    monthly_offers = 0
    status_breakdown = {}
    
    for row in range(2, applications.max_row + 1):
        # v3.0: DateApplied=col9, Status=col10
        date = _normalize_date(applications.cell(row=row, column=9).value)
        status = applications.cell(row=row, column=10).value
        
        if date and date >= one_month_ago:
            monthly_apps += 1
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
            normalized_status = str(status or '').strip().lower()
            if normalized_status == 'interview':
                monthly_interviews += 1
            elif normalized_status == 'offer':
                monthly_offers += 1
    
    # Calculate rates
    response_rate = 0
    if monthly_apps > 0:
        rejected_count = sum(count for status, count in status_breakdown.items()
                             if str(status or '').strip().lower() == 'rejected')
        responses = monthly_interviews + monthly_offers + rejected_count
        response_rate = (responses / monthly_apps) * 100
    
    interview_rate = (monthly_interviews / monthly_apps * 100) if monthly_apps > 0 else 0
    offer_rate = (monthly_offers / monthly_apps * 100) if monthly_apps > 0 else 0
    
    # Generate report
    report = f"""
================================================================================
                    MONTHLY JOB SEARCH REPORT
================================================================================
Report Date: {datetime.now().strftime('%Y-%m-%d')}
Period: Last 30 Days

================================================================================
MONTHLY OVERVIEW
================================================================================
• Total Applications: {monthly_apps}
• Interviews Secured: {monthly_interviews}
• Offers Received: {monthly_offers}
• Response Rate: {response_rate:.1f}%
• Interview Rate: {interview_rate:.1f}%
• Offer Rate: {offer_rate:.1f}%

================================================================================
STATUS BREAKDOWN
================================================================================
"""
    for status, count in status_breakdown.items():
        percentage = (count / monthly_apps * 100) if monthly_apps > 0 else 0
        report += f"• {status}: {count} ({percentage:.1f}%)\n"
    
    report += """
================================================================================
PERFORMANCE ANALYSIS
================================================================================
"""
    
    # Performance insights
    if response_rate > 30:
        report += "✓ Strong response rate - your applications are getting noticed!\n"
    elif response_rate > 20:
        report += "⚠ Good response rate, but room for improvement.\n"
    else:
        report += "⚠ Low response rate - consider improving your resume and cover letters.\n"
    
    if interview_rate > 15:
        report += "✓ Excellent interview conversion rate!\n"
    elif interview_rate > 10:
        report += "⚠ Good interview rate, keep networking to improve.\n"
    else:
        report += "⚠ Low interview rate - focus on skill development and networking.\n"
    
    report += """
================================================================================
NEXT MONTH'S STRATEGY
================================================================================
• Target Companies: Focus on top 10 dream companies
• Application Strategy: Quality over quantity
• Networking: Attend 2 industry events
• Skill Development: Complete 1 online course
• Interview Prep: Practice 50+ technical questions

================================================================================
CreatorDockStudio - Your Job Search Success Partner
================================================================================
"""
    
    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Monthly report generated: {output_path}")
    return report

def main():
    import os as _os
    _base = _os.path.dirname(_os.path.abspath(__file__))
    file_path = _os.path.join(_base, 'Developer_Job_Application_Tracker_PRO.xlsx')
    output_dir = _os.path.join(_base, 'reports')
    _os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    weekly_report_path = f"{output_dir}/weekly_report_{timestamp}.txt"
    monthly_report_path = f"{output_dir}/monthly_report_{timestamp}.txt"
    
    generate_weekly_report(file_path, weekly_report_path)
    generate_monthly_report(file_path, monthly_report_path)
    
    print("\nAll reports generated successfully!")

if __name__ == "__main__":
    main()
