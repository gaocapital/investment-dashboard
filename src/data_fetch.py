import win32com.client
import pandas as pd

def fetch_data(file_name):
    excel = win32com.client.Dispatch("Excel.Application")
    wb = excel.Workbooks.Open(f'./data/{file_name}')
    excel.Visible = False  # Hide Excel window during automation

    # Refresh all queries in the workbook
    wb.RefreshAll()
    
    # Wait until all queries are refreshed (simple polling)
    while excel.Refreshing:
        time.sleep(1)
    
    # Save the workbook after refreshing
    wb.Save()
    
    # Assuming data is on the first sheet; adjust as necessary
    sheet = wb.Sheets[0]
    data = pd.read_excel(f'./data/{file_name}', sheet_name=sheet.Name)

    # Close the workbook and quit Excel
    wb.Close()
    excel.Quit()
    
    return data

