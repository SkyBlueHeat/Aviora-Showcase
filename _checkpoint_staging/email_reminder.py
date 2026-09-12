import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
from html import escape
import os
import openpyxl

# Email Reminder Script for Job Application Tracker
# Sends automated reminders for follow-ups and interviews

def load_applications(file_path):
    """Load applications from Excel file"""
    wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
    ws = wb['Applications']
    return ws

def _to_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y', '%d/%m/%Y'):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                pass
    return None

def get_upcoming_followups(ws, days_ahead=7):
    """Get applications with follow-ups in the next N days"""
    today = datetime.now().date()
    upcoming = []
    
    for row in range(2, ws.max_row + 1):
        # v3.0: FollowupDate=col13, Company=col2, Role=col3, Status=col10
        followup_date = ws.cell(row=row, column=13).value
        company = ws.cell(row=row, column=2).value
        role = ws.cell(row=row, column=3).value
        status = ws.cell(row=row, column=10).value

        followup_date = _to_date(followup_date)
        if followup_date:
            days_until = (followup_date - today).days

            if 0 <= days_until <= days_ahead:
                upcoming.append({
                    'company': company,
                    'role': role,
                    'status': status,
                    'followup_date': followup_date,
                    'days_until': days_until
                })
    
    return upcoming

def check_pending_applications(file_path, days_pending=7):
    """Get applications that have had no terminal response for N+ days."""
    ws = load_applications(file_path)
    today = datetime.now().date()
    pending = []
    terminal_keywords = ('interview', 'offer', 'rejected', 'withdrawn', 'declined', 'accepted', 'hired')

    for row in range(2, ws.max_row + 1):
        # v3.0: Company=col2, Role=col3, DateApplied=col9, Status=col10, FollowupDate=col13
        company = ws.cell(row=row, column=2).value
        role = ws.cell(row=row, column=3).value
        applied_date = _to_date(ws.cell(row=row, column=9).value)
        status = ws.cell(row=row, column=10).value
        followup_date = _to_date(ws.cell(row=row, column=13).value)
        status_text = str(status or '').strip().lower()

        if not company or not role or not applied_date:
            continue
        if any(keyword in status_text for keyword in terminal_keywords):
            continue
        if followup_date and followup_date > today:
            continue

        days_since = (today - applied_date).days
        if days_since >= days_pending:
            pending.append({
                'company': company,
                'role': role,
                'status': status or 'Applied',
                'applied_date': applied_date,
                'followup_date': followup_date,
                'days_pending': days_since,
            })

    return pending

def _build_rows(items, mode):
    rows = []
    for item in items:
        company = escape(str(item.get('company') or 'Unknown'))
        role = escape(str(item.get('role') or 'Unknown'))
        status = escape(str(item.get('status') or 'Applied'))
        if mode == 'pending':
            applied_date = item.get('applied_date')
            applied_text = applied_date.isoformat() if isinstance(applied_date, date) else 'N/A'
            rows.append(
                f"""
            <tr>
                <td>{company}</td>
                <td>{role}</td>
                <td>{status}</td>
                <td>{applied_text}</td>
                <td>{item.get('days_pending', 0)} days</td>
            </tr>
        """
            )
        else:
            followup_date = item.get('followup_date')
            followup_text = followup_date.isoformat() if isinstance(followup_date, date) else 'N/A'
            rows.append(
                f"""
            <tr>
                <td>{company}</td>
                <td>{role}</td>
                <td>{status}</td>
                <td>{followup_text}</td>
                <td>{item.get('days_until', 0)} days</td>
            </tr>
        """
            )
    return ''.join(rows)

def send_reminder_email(arg1, arg2, smtp_config):
    """Send reminder email with upcoming follow-ups"""
    if isinstance(arg1, dict):
        followups = [arg1]
        to_email = arg2
        subject_prefix = 'Pending Application Reminder'
        intro = 'You have pending applications that may need a follow-up:'
        mode = 'pending'
        date_header = 'Applied Date'
        days_header = 'Days Pending'
    else:
        to_email = arg1
        followups = list(arg2 or [])
        subject_prefix = 'Job Search Follow-up Reminders'
        intro = 'You have the following follow-ups coming up:'
        mode = 'followup'
        date_header = 'Follow-up Date'
        days_header = 'Days Until'

    if not to_email:
        raise ValueError('Recipient email address is required.')
    if not followups:
        print('No reminder items to send.')
        return

    msg = MIMEMultipart()
    msg['From'] = smtp_config['from_email']
    msg['To'] = to_email
    msg['Subject'] = f"{subject_prefix} - {datetime.now().strftime('%Y-%m-%d')}"
    
    body = """
    <html>
    <body>
        <h2>📋 Job Search Follow-up Reminders</h2>
        <p>{intro}</p>
        <table border="1" cellpadding="10" cellspacing="0">
            <tr>
                <th>Company</th>
                <th>Role</th>
                <th>Status</th>
                <th>{date_header}</th>
                <th>{days_header}</th>
            </tr>
    """.format(intro=escape(intro), date_header=escape(date_header), days_header=escape(days_header))
    body += _build_rows(followups, mode)
    
    body += """
        </table>
        <p>Stay organized and land your dream job! 🚀</p>
        <p><em>CreatorDockStudio Job Application Tracker</em></p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html', 'utf-8'))
    
    server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'], timeout=30)
    server.starttls()
    server.login(smtp_config['username'], smtp_config['password'])
    server.send_message(msg)
    server.quit()
    
    print(f"Reminder email sent to {to_email}")

def main():
    _base = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(_base, 'Developer_Job_Application_Tracker_PRO.xlsx')
    to_email = os.environ.get('EMAIL_REMINDER_TO', '').strip()
    from_email = os.environ.get('EMAIL_REMINDER_FROM', '').strip()
    password = os.environ.get('EMAIL_REMINDER_PASSWORD', '').strip()
    
    smtp_config = {
        'from_email': from_email,
        'smtp_server': os.environ.get('EMAIL_REMINDER_SMTP_SERVER', 'smtp.gmail.com').strip(),
        'smtp_port': int(os.environ.get('EMAIL_REMINDER_SMTP_PORT', '587')),
        'username': from_email,
        'password': password,
    }

    if not to_email or not from_email or not password:
        print('Set EMAIL_REMINDER_TO, EMAIL_REMINDER_FROM, and EMAIL_REMINDER_PASSWORD before running this script directly.')
        return
    
    ws = load_applications(file_path)
    followups = get_upcoming_followups(ws, days_ahead=7)
    
    if followups:
        print(f"Found {len(followups)} upcoming follow-ups")
        send_reminder_email(to_email, followups, smtp_config)
    else:
        print("No upcoming follow-ups in the next 7 days")

if __name__ == "__main__":
    main()
