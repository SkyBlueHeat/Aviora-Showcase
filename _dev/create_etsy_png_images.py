from PIL import Image, ImageDraw, ImageFont
import os

# Create directory
os.makedirs('c:/Users/erkay/Desktop/önemli/etsy_png_images', exist_ok=True)

# Colors
BG_COLOR = (245, 245, 245)
CARD_COLOR = (255, 255, 255)
ACCENT_COLOR = (255, 107, 53)
TEXT_COLOR = (34, 34, 34)
SECONDARY_COLOR = (32, 196, 183)

def create_image(filename, title, subtitle, features, icon="📊"):
    img = Image.new('RGB', (1200, 630), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Title
    try:
        font_large = ImageFont.truetype("arial.ttf", 48)
        font_medium = ImageFont.truetype("arial.ttf", 28)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw icon
    draw.text((50, 50), icon, font=font_large, fill=ACCENT_COLOR)
    
    # Draw title
    draw.text((120, 50), title, font=font_large, fill=TEXT_COLOR)
    
    # Draw subtitle
    draw.text((120, 110), subtitle, font=font_medium, fill=(100, 100, 100))
    
    # Draw features
    y = 180
    for feature in features:
        draw.text((50, y), "✓ " + feature, font=font_small, fill=TEXT_COLOR)
        y += 40
    
    # Draw card at bottom
    draw.rectangle([50, y + 20, 1150, 580], fill=CARD_COLOR, outline=(200, 200, 200))
    draw.text((70, y + 40), "Developer Job Application Tracker PRO", font=font_medium, fill=TEXT_COLOR)
    draw.text((70, y + 80), "Ultimate Bundle • $34.99", font=font_small, fill=ACCENT_COLOR)
    
    img.save(f'c:/Users/erkay/Desktop/önemli/etsy_png_images/{filename}.png')
    print(f"Created {filename}.png")

# Create 10 images
create_image("01_main_cover", 
             "Job Application Tracker PRO",
             "Complete Developer Career Management System",
             ["10 Excel Sheets", "7 Bonus Resources", "Notion Compatible", "Printable Planner"],
             "🚀")

create_image("02_dashboard_preview",
             "Dynamic Dashboard",
             "Real-time KPIs & Analytics",
             ["Applications Sent", "Interview Pipeline", "Offer Conversion", "Weekly Trends"],
             "📊")

create_image("03_application_tracker",
             "Application Tracker",
             "Track 300+ Applications",
             ["Dropdown Menus", "Status Management", "Priority Scoring", "Follow-up Reminders"],
             "📋")

create_image("04_interview_tracker",
             "Interview Tracker",
             "Multi-stage Interview Management",
             ["Recruiter Screen", "Technical Assessment", "Live Coding", "System Design"],
             "🎯")

create_image("05_recruiter_crm",
             "Recruiter CRM",
             "Build Your Professional Network",
             ["Contact Management", "Relationship Scoring", "Follow-up Scheduling", "LinkedIn Integration"],
             "👥")

create_image("06_salary_comparison",
             "Salary Comparison",
             "Negotiate Better Offers",
             ["Total Compensation Calculator", "Benefits Analysis", "Offer Ranking", "Decision Matrix"],
             "💰")

create_image("07_weekly_planner",
             "Weekly Planner",
             "Stay Organized & Focused",
             ["Goal Setting", "Task Management", "Progress Tracking", "Weekly Reflection"],
             "📅")

create_image("08_statistics",
             "Statistics & Analytics",
             "Data-Driven Job Search",
             ["Conversion Rates", "Response Analytics", "Performance Metrics", "Trend Analysis"],
             "📈")

create_image("09_bonus_resources",
             "7 Bonus Resources",
             "$150+ Value Included Free",
             ["100+ Interview Questions", "10 Email Templates", "LinkedIn Guide", "Negotiation Script"],
             "🎁")

create_image("10_notion_compatibility",
             "Notion Compatible",
             "Access From Anywhere",
             ["5 CSV Templates", "Mobile Access", "Collaboration Ready", "Real-time Sync"],
             "📱")

print("\n✅ All 10 PNG images created successfully!")
