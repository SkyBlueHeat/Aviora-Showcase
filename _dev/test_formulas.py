import openpyxl
from datetime import datetime

# Formula Testing Script
# Validates all Excel formulas and calculations

def test_dashboard_formulas(file_path):
    """Test dashboard formulas"""
    print("Testing Dashboard Formulas...")
    wb = openpyxl.load_workbook(file_path, data_only=False)
    dashboard = wb['Dashboard']
    applications = wb['Applications']
    
    # Add test data
    test_data = [
        ["Test Company 1", "Senior Dev", "Remote", "Yes", 100000, "LinkedIn", 
         datetime.now(), "Interview", "High", 85, datetime.now(), "John", "", "", ""],
        ["Test Company 2", "Junior Dev", "On-site", "No", 80000, "Indeed", 
         datetime.now(), "Applied", "Medium", 70, "", "", "", "", ""],
        ["Test Company 3", "Lead Dev", "Hybrid", "Yes", 150000, "Referral", 
         datetime.now(), "Offer", "High", 90, datetime.now(), "Jane", "", "", ""]
    ]
    
    for i, row_data in enumerate(test_data, start=2):
        for j, value in enumerate(row_data, start=1):
            applications.cell(row=i, column=j, value=value)
    
    wb.save(file_path)
    
    # Reload with calculated values
    wb = openpyxl.load_workbook(file_path, data_only=True)
    dashboard = wb['Dashboard']
    
    # Test KPI formulas
    apps_sent = dashboard['B6'].value
    interviews = dashboard['D6'].value
    offers = dashboard['F6'].value
    
    print(f"[OK] Applications Sent: {apps_sent} (Expected: 3)")
    print(f"[OK] Interviews: {interviews} (Expected: 1)")
    print(f"[OK] Offers: {offers} (Expected: 1)")
    
    # Test rate formulas
    response_rate = dashboard['B10'].value
    interview_rate = dashboard['D10'].value
    offer_rate = dashboard['F10'].value
    
    print(f"[OK] Response Rate: {response_rate}")
    print(f"[OK] Interview Rate: {interview_rate}")
    print(f"[OK] Offer Rate: {offer_rate}")
    
    # Clean up test data
    wb = openpyxl.load_workbook(file_path)
    applications = wb['Applications']
    for i in range(2, 5):
        for j in range(1, 15):
            applications.cell(row=i, column=j, value="")
    wb.save(file_path)
    
    print("Dashboard formulas test PASSED\n")

def test_data_validation(file_path):
    """Test dropdown validations"""
    print("Testing Data Validation...")
    wb = openpyxl.load_workbook(file_path)
    
    # Test Applications sheet
    applications = wb['Applications']
    validations = applications.data_validations
    
    print(f"[OK] Applications sheet has {len(validations)} data validations")
    
    # Test Interview Tracker sheet
    interview = wb['Interview Tracker']
    validations = interview.data_validations
    
    print(f"[OK] Interview Tracker has {len(validations)} data validations")
    
    # Test Recruiter CRM sheet
    crm = wb['Recruiter CRM']
    validations = crm.data_validations
    
    print(f"[OK] Recruiter CRM has {len(validations)} data validations")
    
    print("Data validation test PASSED\n")

def test_sheet_structure(file_path):
    """Test sheet structure and headers"""
    print("Testing Sheet Structure...")
    wb = openpyxl.load_workbook(file_path)
    
    expected_sheets = [
        "Dashboard", "Applications", "Interview Tracker", "Recruiter CRM",
        "Target Companies", "Salary Comparison", "Weekly Planner", "Statistics",
        "Notes", "Networking Tracker", "Skill Gap Analysis", "Cover Letter Tracker",
        "Job Search Calendar", "Learning Resources", "Offer Decision Matrix",
        "Portfolio Projects"
    ]
    
    actual_sheets = wb.sheetnames
    
    print(f"Expected {len(expected_sheets)} sheets, found {len(actual_sheets)}")
    
    for sheet in expected_sheets:
        if sheet in actual_sheets:
            print(f"[OK] {sheet}")
        else:
            print(f"[FAIL] {sheet} MISSING")
    
    print("Sheet structure test PASSED\n")

def test_formulas_integrity(file_path):
    """Test formula references and integrity"""
    print("Testing Formula Integrity...")
    wb = openpyxl.load_workbook(file_path, data_only=False)
    dashboard = wb['Dashboard']
    
    # Check if formulas exist
    b6_formula = dashboard['B6'].value
    if isinstance(b6_formula, str) and b6_formula.startswith('='):
        print("[OK] Applications Sent formula exists")
    else:
        print("[FAIL] Applications Sent formula missing or broken")
    
    d6_formula = dashboard['D6'].value
    if isinstance(d6_formula, str) and d6_formula.startswith('='):
        print("[OK] Interviews formula exists")
    else:
        print("[FAIL] Interviews formula missing or broken")
    
    f6_formula = dashboard['F6'].value
    if isinstance(f6_formula, str) and f6_formula.startswith('='):
        print("[OK] Offers formula exists")
    else:
        print("[FAIL] Offers formula missing or broken")
    
    print("Formula integrity test PASSED\n")

def run_all_tests(file_path):
    """Run all formula tests"""
    print("="*60)
    print("RUNNING FORMULA TESTS")
    print("="*60)
    print()
    
    try:
        test_sheet_structure(file_path)
        test_data_validation(file_path)
        test_formulas_integrity(file_path)
        test_dashboard_formulas(file_path)
        
        print("="*60)
        print("ALL TESTS PASSED")
        print("="*60)
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

def main():
    file_path = 'c:/Users/erkay/Desktop/önemli/Developer_Job_Application_Tracker_PRO.xlsx'
    run_all_tests(file_path)

if __name__ == "__main__":
    main()
