import os

# Create images directory
os.makedirs('c:/Users/erkay/Desktop/önemli/etsy_images', exist_ok=True)

# SVG templates for 10 different Etsy listing images
images = [
    {
        "filename": "01_main_cover.svg",
        "title": "Developer Job Application Tracker PRO",
        "subtitle": "Premium Excel Dashboard",
        "features": ["300+ Applications", "Auto Metrics", "Interview Tracker"]
    },
    {
        "filename": "02_dashboard_preview.svg",
        "title": "Live Dashboard",
        "subtitle": "Real-time KPIs & Analytics",
        "features": ["Response Rates", "Salary Tracking", "Pipeline View"]
    },
    {
        "filename": "03_application_tracker.svg",
        "title": "Application Tracker",
        "subtitle": "Track Every Opportunity",
        "features": ["Status Updates", "Follow-up Reminders", "Priority Scoring"]
    },
    {
        "filename": "04_interview_tracker.svg",
        "title": "Interview Tracker",
        "subtitle": "Ace Every Interview",
        "features": ["Stage Tracking", "Prep Notes", "Lessons Learned"]
    },
    {
        "filename": "05_recruiter_crm.svg",
        "title": "Recruiter CRM",
        "subtitle": "Build Your Network",
        "features": ["Contact Management", "Follow-up System", "Relationship Scoring"]
    },
    {
        "filename": "06_salary_comparison.svg",
        "title": "Salary Comparison",
        "subtitle": "Compare Offers Like a Pro",
        "features": ["Total Comp Calculator", "Benefits Analysis", "Decision Matrix"]
    },
    {
        "filename": "07_weekly_planner.svg",
        "title": "Weekly Planner",
        "subtitle": "Stay Organized",
        "features": ["Goal Setting", "Progress Tracking", "Weekly Reflection"]
    },
    {
        "filename": "08_statistics.svg",
        "title": "Job Search Statistics",
        "subtitle": "Data-Driven Job Hunt",
        "features": ["Conversion Rates", "Trend Analysis", "Target Tracking"]
    },
    {
        "filename": "09_benefits.svg",
        "title": "Why This Tracker?",
        "subtitle": "Built for Developers",
        "features": ["Save 10+ Hours/Week", "Never Miss Follow-up", "Land Your Dream Job"]
    },
    {
        "filename": "10_workflow.svg",
        "title": "Complete Workflow",
        "subtitle": "From Application to Offer",
        "features": ["All-in-One System", "Professional Design", "Instant Download"]
    }
]

# SVG template with Apple-inspired design
svg_template = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="2000" height="2000" viewBox="0 0 2000 2000" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFFFFF;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#F5F5F5;stop-opacity:1" />
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="10" stdDeviation="20" flood-color="#000000" flood-opacity="0.1"/>
    </filter>
  </defs>
  
  <!-- Background -->
  <rect width="2000" height="2000" fill="url(#bgGradient)"/>
  
  <!-- Decorative Elements -->
  <circle cx="1700" cy="300" r="200" fill="#FF6B35" opacity="0.1"/>
  <circle cx="300" cy="1700" r="150" fill="#20C4B7" opacity="0.1"/>
  
  <!-- Main Card -->
  <rect x="200" y="200" width="1600" height="1600" rx="40" fill="#FFFFFF" filter="url(#shadow)"/>
  
  <!-- Accent Bar -->
  <rect x="200" y="200" width="1600" height="12" rx="6" fill="#FF6B35"/>
  
  <!-- Title -->
  <text x="1000" y="500" font-family="Segoe UI, Arial, sans-serif" font-size="72" font-weight="bold" fill="#222222" text-anchor="middle">{title}</text>
  
  <!-- Subtitle -->
  <text x="1000" y="600" font-family="Segoe UI, Arial, sans-serif" font-size="42" fill="#666666" text-anchor="middle">{subtitle}</text>
  
  <!-- Feature Cards -->
  <rect x="300" y="750" width="500" height="200" rx="20" fill="#F5F5F5"/>
  <text x="550" y="880" font-family="Segoe UI, Arial, sans-serif" font-size="36" font-weight="bold" fill="#FF6B35" text-anchor="middle">{feature1}</text>
  
  <rect x="750" y="750" width="500" height="200" rx="20" fill="#F5F5F5"/>
  <text x="1000" y="880" font-family="Segoe UI, Arial, sans-serif" font-size="36" font-weight="bold" fill="#20C4B7" text-anchor="middle">{feature2}</text>
  
  <rect x="1200" y="750" width="500" height="200" rx="20" fill="#F5F5F5"/>
  <text x="1450" y="880" font-family="Segoe UI, Arial, sans-serif" font-size="36" font-weight="bold" fill="#FF6B35" text-anchor="middle">{feature3}</text>
  
  <!-- Dashboard Mockup -->
  <rect x="300" y="1050" width="1400" height="600" rx="20" fill="#222222"/>
  <rect x="320" y="1070" width="1360" height="560" rx="15" fill="#FFFFFF"/>
  
  <!-- Mockup Dashboard Elements -->
  <rect x="350" y="1100" width="300" height="150" rx="10" fill="#F5F5F5"/>
  <text x="500" y="1180" font-family="Segoe UI, Arial, sans-serif" font-size="24" fill="#222222" text-anchor="middle">Applications</text>
  <text x="500" y="1220" font-family="Segoe UI, Arial, sans-serif" font-size="36" font-weight="bold" fill="#FF6B35" text-anchor="middle">127</text>
  
  <rect x="700" y="1100" width="300" height="150" rx="10" fill="#F5F5F5"/>
  <text x="850" y="1180" font-family="Segoe UI, Arial, sans-serif" font-size="24" fill="#222222" text-anchor="middle">Interviews</text>
  <text x="850" y="1220" font-family="Segoe UI, Arial, sans-serif" font-size="36" font-weight="bold" fill="#20C4B7" text-anchor="middle">23</text>
  
  <rect x="1050" y="1100" width="300" height="150" rx="10" fill="#F5F5F5"/>
  <text x="1200" y="1180" font-family="Segoe UI, Arial, sans-serif" font-size="24" fill="#222222" text-anchor="middle">Offers</text>
  <text x="1200" y="1220" font-family="Segoe UI, Arial, sans-serif" font-size="36" font-weight="bold" fill="#FF6B35" text-anchor="middle">4</text>
  
  <rect x="1350" y="1100" width="300" height="150" rx="10" fill="#F5F5F5"/>
  <text x="1500" y="1180" font-family="Segoe UI, Arial, sans-serif" font-size="24" fill="#222222" text-anchor="middle">Response Rate</text>
  <text x="1500" y="1220" font-family="Segoe UI, Arial, sans-serif" font-size="36" font-weight="bold" fill="#20C4B7" text-anchor="middle">38%</text>
  
  <!-- Chart Mockup -->
  <rect x="350" y="1300" width="700" height="300" rx="10" fill="#F5F5F5"/>
  <text x="700" y="1350" font-family="Segoe UI, Arial, sans-serif" font-size="20" fill="#666666" text-anchor="middle">Application Pipeline</text>
  <circle cx="450" cy="1500" r="60" fill="#FF6B35"/>
  <circle cx="600" cy="1500" r="50" fill="#20C4B7"/>
  <circle cx="730" cy="1500" r="40" fill="#FF6B35" opacity="0.6"/>
  <circle cx="850" cy="1500" r="30" fill="#20C4B7" opacity="0.6"/>
  
  <!-- List Mockup -->
  <rect x="1100" y="1300" width="550" height="300" rx="10" fill="#F5F5F5"/>
  <text x="1375" y="1350" font-family="Segoe UI, Arial, sans-serif" font-size="20" fill="#666666" text-anchor="middle">Recent Activity</text>
  <rect x="1130" y="1380" width="490" height="40" rx="5" fill="#FFFFFF"/>
  <rect x="1130" y="1430" width="490" height="40" rx="5" fill="#FFFFFF"/>
  <rect x="1130" y="1480" width="490" height="40" rx="5" fill="#FFFFFF"/>
  <rect x="1130" y="1530" width="490" height="40" rx="5" fill="#FFFFFF"/>
  
  <!-- Brand Footer -->
  <text x="1000" y="1850" font-family="Segoe UI, Arial, sans-serif" font-size="28" fill="#999999" text-anchor="middle">CreatorDockStudio</text>
</svg>'''

# Generate all 10 images
for img in images:
    svg_content = svg_template.format(
        title=img['title'],
        subtitle=img['subtitle'],
        feature1=img['features'][0],
        feature2=img['features'][1],
        feature3=img['features'][2]
    )
    
    filepath = f"c:/Users/erkay/Desktop/önemli/etsy_images/{img['filename']}"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Created: {img['filename']}")

print("\nAll 10 Etsy listing images created successfully!")
