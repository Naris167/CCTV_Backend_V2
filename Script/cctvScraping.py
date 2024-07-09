import requests
import pandas as pd
import re
import ast
import os
from datetime import datetime

# URL to connect to
url = "http://www.bmatraffic.com/index.aspx"
master_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cctv_locations_master.xlsx')
data_folder = os.path.join(os.path.dirname(__file__), '..', 'data')

# Function to extract and process CCTV data from the webpage
def extract_cctv_data(url):
    print(f"\nConnecting to {url}")
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful

    # Find the var locations = [...] data
    data_pattern = re.compile(r"var locations = (\[.*?\]);", re.DOTALL)
    match = data_pattern.search(response.text)

    if match:
        data_string = match.group(1)
        
        # Convert the JavaScript array to a Python list using ast.literal_eval
        json_data = ast.literal_eval(data_string)

        # Process data to use the specified column names
        processed_data = []
        for item in json_data:
            code_match = re.match(r'^[A-Z0-9\-]+', item[1])
            code = code_match.group(0) if code_match else ''
            cam_name = item[1][len(code):].strip() if code else item[1]
            
            processed_item = [
                item[0],       # ID
                code,          # Code
                cam_name,      # Cam_Name
                item[2],       # Cam_Name_e
                item[3],       # Cam_Location
                item[4],       # Cam_Direction
                item[5],       # Latitude
                item[6],       # Longitude
                item[7],       # IP
                item[8]        # Icon
            ]
            processed_data.append(processed_item)
        
        # Create a DataFrame with the specified column names
        columns = ["ID", "Code", "Cam_Name", "Cam_Name_e", "Cam_Location", "Cam_Direction", "Latitude", "Longitude", "IP", "Icon"]
        df = pd.DataFrame(processed_data, columns=columns)
        
        return df
    else:
        print("Data not found")
        return None

# Function to remove duplicates by comparing with master file
def remove_duplicates(new_df, master_file_path):
    if not os.path.exists(master_file_path):
        print(f"Master file {master_file_path} not found. No duplicates to remove.")
        return new_df
    master_df = pd.read_excel(master_file_path)

    # Ensure 'ID' columns are of the same type
    new_df['ID'] = new_df['ID'].astype(str)
    master_df['ID'] = master_df['ID'].astype(str)
    
    # Remove duplicates
    filtered_df = new_df[~new_df['ID'].isin(master_df['ID'])]
    return filtered_df

# Function to save the data to an Excel file
def save_to_excel(df, folder_path):
    timestamp = datetime.now().strftime("%Y_%m_%d_%I_%M_%S%p")
    filename = f"cctv_locations_additional_{timestamp}.xlsx"
    file_path = os.path.join(folder_path, filename)
    df.to_excel(file_path, index=False)
    print(f"Data saved to {file_path}\n")

# Main function to run the script
def main():
    new_df = extract_cctv_data(url)
    if new_df is not None:
        print("\nGot the CCTV list now!")
        filtered_df = remove_duplicates(new_df, master_file_path)
        print("\nChecking with master record and removing duplicate record\n")
        save_to_excel(filtered_df, data_folder)

if __name__ == "__main__":
    main()
