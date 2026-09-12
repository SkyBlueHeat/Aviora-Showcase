import os
import shutil
import zipfile
from datetime import datetime

# Package Builder Script
# Automatically builds the complete product delivery package

def create_directory_structure(base_dir):
    """Create the standard directory structure"""
    directories = [
        '01_Main_Product',
        '02_Etsy_Images',
        '03_Guides',
        '04_Bonus_Resources',
        '05_Notion_Templates',
        '06_Printable_Planner',
        '07_Scripts',
        '08_Charts_Reports'
    ]
    
    for directory in directories:
        dir_path = os.path.join(base_dir, directory)
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {directory}")

def copy_main_product(source_dir, dest_dir):
    """Copy the main Excel file"""
    source_file = os.path.join(source_dir, 'Developer_Job_Application_Tracker_PRO.xlsx')
    dest_file = os.path.join(dest_dir, '01_Main_Product', 'Developer_Job_Application_Tracker_PRO.xlsx')
    
    if os.path.exists(source_file):
        shutil.copy2(source_file, dest_file)
        print(f"Copied main product: Developer_Job_Application_Tracker_PRO.xlsx")
    else:
        print(f"Warning: Main product file not found at {source_file}")

def copy_etsy_images(source_dir, dest_dir):
    """Copy Etsy images"""
    source_etsy_dir = os.path.join(source_dir, 'etsy_images')
    dest_etsy_dir = os.path.join(dest_dir, '02_Etsy_Images')
    
    if os.path.exists(source_etsy_dir):
        for file in os.listdir(source_etsy_dir):
            if file.endswith('.svg') or file.endswith('.png'):
                shutil.copy2(os.path.join(source_etsy_dir, file), 
                           os.path.join(dest_etsy_dir, file))
        print(f"Copied Etsy images")
    else:
        print(f"Warning: Etsy images directory not found")

def copy_guides(source_dir, dest_dir):
    """Copy guide files"""
    guide_files = [
        'README.md',
        'LICENSE.txt',
        'QUICK_START_GUIDE.txt',
        'FAQ.txt',
        'USER_GUIDE.txt',
        'ADVANCED_USER_GUIDE.txt',
        'VERSION_HISTORY.txt',
        'SUPPORT_SYSTEM_GUIDE.txt',
        'BRAND_GUIDELINES.txt'
    ]
    
    for guide_file in guide_files:
        source_file = os.path.join(source_dir, guide_file)
        dest_file = os.path.join(dest_dir, '03_Guides', guide_file)
        
        if os.path.exists(source_file):
            shutil.copy2(source_file, dest_file)
            print(f"Copied guide: {guide_file}")

def copy_bonus_resources(source_dir, dest_dir):
    """Copy bonus resource files"""
    bonus_files = [
        'BONUS_INTERVIEW_QUESTIONS.txt',
        'BONUS_EMAIL_TEMPLATES.txt',
        'LINKEDIN_OPTIMIZATION_GUIDE.txt',
        'TECHNICAL_INTERVIEW_CHECKLIST.txt',
        'SALARY_NEGOTIATION_SCRIPT.txt',
        'COMPANY_RESEARCH_TEMPLATE.txt',
        'PORTFOLIO_PROJECT_TRACKER.txt',
        'MARKETING_VIDEO_SCRIPTS.txt',
        'SOCIAL_MEDIA_TEMPLATES.txt',
        'EMAIL_MARKETING_TEMPLATES.txt',
        'ETSY_SEO_PACKAGE_V2.txt',
        'CONTENT_MARKETING_GUIDE.txt',
        'PREMIUM_TIER_STRATEGY.txt',
        'TRUST_SIGNALS_GUIDE.txt',
        'LANDING_PAGE_COPY.txt',
        'COMPLETE_ETSY_LISTING.txt'
    ]
    
    for bonus_file in bonus_files:
        source_file = os.path.join(source_dir, bonus_file)
        dest_file = os.path.join(dest_dir, '04_Bonus_Resources', bonus_file)
        
        if os.path.exists(source_file):
            shutil.copy2(source_file, dest_file)
            print(f"Copied bonus resource: {bonus_file}")

def copy_notion_templates(source_dir, dest_dir):
    """Copy Notion templates"""
    source_notion_dir = os.path.join(source_dir, 'notion_templates')
    dest_notion_dir = os.path.join(dest_dir, '05_Notion_Templates')
    
    if os.path.exists(source_notion_dir):
        for file in os.listdir(source_notion_dir):
            if file.endswith('.csv') or file.endswith('.txt'):
                shutil.copy2(os.path.join(source_notion_dir, file), 
                           os.path.join(dest_notion_dir, file))
        
        # Copy Notion setup guide
        setup_guide = os.path.join(source_dir, 'NOTION_SETUP_GUIDE.txt')
        if os.path.exists(setup_guide):
            shutil.copy2(setup_guide, os.path.join(dest_notion_dir, 'NOTION_SETUP_GUIDE.txt'))
        
        print(f"Copied Notion templates")
    else:
        print(f"Warning: Notion templates directory not found")

def copy_scripts(source_dir, dest_dir):
    """Copy Python scripts"""
    script_sources = {
        'auto_backup.py': ['auto_backup.py'],
        'email_reminder.py': ['email_reminder.py'],
        'data_export.py': ['data_export.py'],
        'chart_generator.py': ['chart_generator.py'],
        'report_generator.py': ['report_generator.py'],
        'sync_notion.py': ['sync_notion.py', os.path.join('_dev', 'sync_notion.py')],
        'test_formulas.py': [os.path.join('_dev', 'test_formulas.py'), 'test_formulas.py'],
        'validate_data.py': ['validate_data.py'],
        'ats_resume_checker.py': ['ats_resume_checker.py'],
        'job_description_analyzer.py': ['job_description_analyzer.py'],
        'cover_letter_generator.py': ['cover_letter_generator.py'],
        'interview_prep.py': ['interview_prep.py'],
        'linkedin_message_generator.py': ['linkedin_message_generator.py'],
        'salary_calculator.py': ['salary_calculator.py'],
        'streak_tracker.py': ['streak_tracker.py'],
        'launcher.py': ['launcher.py'],
        'settings.py': ['settings.py'],
        'i18n.py': ['i18n.py'],
        'requirements.txt': ['requirements.txt'],
    }

    for output_name, candidates in script_sources.items():
        source_file = None
        for candidate in candidates:
            candidate_path = os.path.join(source_dir, candidate)
            if os.path.exists(candidate_path):
                source_file = candidate_path
                break

        dest_file = os.path.join(dest_dir, '07_Scripts', output_name)

        if source_file:
            shutil.copy2(source_file, dest_file)
            print(f"Copied script: {output_name}")
        else:
            print(f"Warning: Script not found for package: {output_name}")

def create_readme(dest_dir):
    """Create package README"""
    readme_content = """
================================================================================
                DEVELOPER JOB APPLICATION TRACKER PRO
                        PRODUCT DELIVERY PACKAGE
================================================================================

Thank you for purchasing the Developer Job Application Tracker PRO!
This package contains everything you need to organize your job search.

================================================================================
PACKAGE CONTENTS
================================================================================

📁 01_Main_Product
- Developer_Job_Application_Tracker_PRO.xlsx
  * 16 Integrated Sheets
  * Automatic Formulas
  * Dropdown Menus
  * Premium Design

📁 02_Etsy_Images
- 10 Professional SVG images for Etsy listings

📁 03_Guides
- README.md - Product Overview
- LICENSE.txt - License Agreement
- QUICK_START_GUIDE.txt - 5-Minute Setup
- FAQ.txt - Frequently Asked Questions
- USER_GUIDE.txt - Comprehensive Manual
- VERSION_HISTORY.txt - Version Tracking

📁 04_Bonus_Resources
- 100+ Interview Questions
- 10 Professional Email Templates
- LinkedIn Optimization Guide
- Technical Interview Checklist
- Salary Negotiation Script
- Company Research Template
- Portfolio Project Tracker

📁 05_Notion_Templates
- CSV templates for Notion import
- Notion Setup Guide

📁 06_Printable_Planner
- Printable planner templates

📁 07_Scripts
- Auto Backup Script
- Email Reminder Script
- Data Export Script
- Chart Generator Script
- Report Generator Script
- Notion Sync Script
- Formula Testing Script
- Data Validation Script

📁 08_Charts_Reports
- Directory for generated charts and reports

================================================================================
GETTING STARTED
================================================================================

1. Open Developer_Job_Application_Tracker_PRO.xlsx
2. Read QUICK_START_GUIDE.txt
3. Add your first application
4. Explore the Dashboard
5. Use bonus resources to enhance your job search

================================================================================
SUPPORT
================================================================================

For support Etsy messages: CreatorDockStudio
Response time: 24-48 hours

================================================================================
VERSION
================================================================================

Version: 2.0
Release Date: 2026

================================================================================
CreatorDockStudio
Premium Digital Products for Developers
================================================================================
"""
    
    readme_path = os.path.join(dest_dir, 'README.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"Created package README")

def verify_package_contents(build_dir):
    """Verify required runtime files exist before zipping."""
    required_files = [
        os.path.join('01_Main_Product', 'Developer_Job_Application_Tracker_PRO.xlsx'),
        os.path.join('07_Scripts', 'launcher.py'),
        os.path.join('07_Scripts', 'settings.py'),
        os.path.join('07_Scripts', 'sync_notion.py'),
        os.path.join('07_Scripts', 'auto_backup.py'),
        os.path.join('07_Scripts', 'email_reminder.py'),
        os.path.join('07_Scripts', 'requirements.txt'),
    ]

    missing = []
    for rel_path in required_files:
        if not os.path.exists(os.path.join(build_dir, rel_path)):
            missing.append(rel_path)

    if missing:
        raise FileNotFoundError('Missing package files: ' + ', '.join(missing))

    print('Verified package contents')

def create_zip_package(source_dir, output_dir):
    """Create ZIP package"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"Developer_Job_Application_Tracker_PRO_v2.0_{timestamp}.zip"
    zip_path = os.path.join(output_dir, zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    
    print(f"\n✓ ZIP package created: {zip_name}")
    print(f"  Location: {zip_path}")
    
    # Get file size
    file_size = os.path.getsize(zip_path) / (1024 * 1024)  # Convert to MB
    print(f"  Size: {file_size:.2f} MB")
    
    return zip_path

def build_package(source_dir, output_dir):
    """Build complete package"""
    print("="*60)
    print("BUILDING PRODUCT DELIVERY PACKAGE")
    print("="*60)
    print()
    
    # Create temporary build directory
    build_dir = os.path.join(output_dir, 'build_temp')
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    
    os.makedirs(build_dir, exist_ok=True)
    
    # Create directory structure
    create_directory_structure(build_dir)
    
    # Copy all files
    copy_main_product(source_dir, build_dir)
    copy_etsy_images(source_dir, build_dir)
    copy_guides(source_dir, build_dir)
    copy_bonus_resources(source_dir, build_dir)
    copy_notion_templates(source_dir, build_dir)
    copy_scripts(source_dir, build_dir)
    
    # Create README
    create_readme(build_dir)
    verify_package_contents(build_dir)
    
    # Create ZIP package
    zip_path = create_zip_package(build_dir, output_dir)
    
    # Clean up temporary directory
    shutil.rmtree(build_dir)
    
    print("\n" + "="*60)
    print("PACKAGE BUILD COMPLETED SUCCESSFULLY ✓")
    print("="*60)
    
    return zip_path

def main():
    source_dir = 'c:/Users/erkay/Desktop/önemli'
    output_dir = 'c:/Users/erkay/Desktop/önemli/releases'
    
    os.makedirs(output_dir, exist_ok=True)
    
    build_package(source_dir, output_dir)

if __name__ == "__main__":
    main()
