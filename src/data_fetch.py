import time
import pandas as pd
from pathlib import Path
import win32com.client

def fetch_data(file_name):
    # Get the absolute file path
    base_dir = Path(__file__).parent.parent
    file_path = base_dir / 'data' / file_name
    file_path_str = str(file_path.resolve())

    # Initialize Excel application
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False 

    try:
        # Open the workbook
        wb = excel.Workbooks.Open(file_path_str)
    except Exception as e:
        print(f"Error opening workbook: {e}")
        excel.Quit()
        return None

    # Refresh all queries in the workbook
    wb.RefreshAll()

    # Wait for all QueryTables to finish refreshing
    wait_for_refresh(wb)

    # Save the workbook (optional if you need to save changes)
    wb.Save()

    # Assuming the first sheet contains the data
    sheet = wb.Sheets(1)
    # Read the data from the first sheet into a pandas DataFrame
    data = pd.read_excel(file_path_str, sheet_name=sheet.Name)

    # Close the workbook and quit the Excel application
    wb.Close()
    excel.Quit()

    return data

def wait_for_refresh(workbook, timeout=30):
    """ Wait for all QueryTables to finish refreshing """
    start_time = time.time()
    while True:
        refreshing = False
        for sheet in workbook.Sheets:
            try:
                # Loop through all QueryTables in the sheet
                for qt in sheet.QueryTables:
                    if qt.Refreshing:  # Check if a query is still refreshing
                        refreshing = True
                        break
                if refreshing:
                    break
            except Exception:
                # Some sheets might not have QueryTables (like regular data)
                continue

        # If no QueryTable is refreshing, we're done
        if not refreshing:
            break

        # Timeout logic if refresh takes too long
        if time.time() - start_time > timeout:
            print("Warning: Timeout waiting for refresh.")
            break

        # Wait for a short period before checking again
        time.sleep(1)
