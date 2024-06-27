#!/usr/bin/env python3
import os
import shutil
import tempfile
import requests
import zipfile
import csv
from bs4 import BeautifulSoup
from datetime import datetime
def extract_percentage_from_hocr(hocr_file):
    print(f"Extracting percentage from HOCR file: {hocr_file}")
    with open(hocr_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        meta = soup.find('meta', attrs={'name': 'ocr-system'})
        if meta:
            print(f"Meta tag found: {meta}")
            if 'extract-percentage' in meta.attrs:
                percentage_str = meta['extract-percentage']
                print(f"Extracted percentage: {percentage_str}")
                return float(percentage_str)
        print("No extract percentage found in meta tag")
        return None
def extract_page_number_from_filename(filename):
    print(f"Extracting page number from filename: {filename}")
    base_name = os.path.splitext(filename)[0]
    try:
        # Split by the first dot (.) from the right
        split_by_dot = base_name.rsplit('.', 1)
        # Split the left part by the second dot (.) from the left
        page_number = split_by_dot[0].rsplit('.', 1)[1]
        print(f"Extracted page number: {page_number}")
        return int(page_number) + 1
    except (IndexError, ValueError) as e:
        print(f"Error extracting page number from filename: {e}")
        return None
def main():
    # Determine the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Source directory containing the files to be processed
    source_dir = os.path.join(script_dir, 'src/test/results')
    # Ensure the source directory exists
    if not os.path.exists(source_dir) or not os.path.isdir(source_dir):
        print("Source directory does not exist")
        exit(1)
    url = 'http://localhost:9901/pdfbox-utilities/convert'
    csv_data = []
    for filename in os.listdir(source_dir):
        source_file = os.path.join(source_dir, filename)
        if os.path.isfile(source_file):
            print(f"Processing file: {filename}")
            # Create a unique temp directory for each file
            temp_dir_suffix = f"temp_dir_{filename}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            work_dir = tempfile.mkdtemp(suffix=temp_dir_suffix, dir=script_dir)
            os.chmod(work_dir, 0o777)
            # Copy the source file to the unique temp directory
            shutil.copy(source_file, work_dir)
            # Construct the files dictionary for the POST request
            file_path = os.path.join(work_dir, filename)
            files = {filename: (filename, open(file_path, 'rb'))}
            response = requests.post(url, files=files)
            if response.status_code == 200:
                print(f"POST request successful for {filename}")
            else:
                print(f"POST request failed for {filename} with status code {response.status_code}")
                continue
            # Save the response content to a zip file
            zip_path = os.path.join(work_dir, 'downloaded.files.zip')
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            # Unzip the downloaded files
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(work_dir)
            # Process the extracted files and gather required data
            for root, _, files in os.walk(work_dir):
                for file in files:
                    if file.endswith('.hocr.html'):
                        print(f"Processing HOCR file: {file}")
                        hocr_file = os.path.join(root, file)
                        percentage = extract_percentage_from_hocr(hocr_file)
                        if percentage is not None:
                            page_number = extract_page_number_from_filename(file)
                            if page_number is not None:
                                # Append temp_dir_suffix instead of work_dir
                                csv_data.append([filename, temp_dir_suffix, page_number, percentage])
                                print(f"Added data for page {page_number} with percentage {percentage}")
    
    # Sort csv_data by page number
    csv_data.sort(key=lambda x: x[2])
    # Generate a unique CSV file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file_path = os.path.join(script_dir, f'output_data_{timestamp}.csv')
    with open(csv_file_path, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['source file', 'output dir', 'page number', 'text percentage'])
        csv_writer.writerows(csv_data)
    print(f"CSV file generated at {csv_file_path}.")
    print(f"Processing for {filename} completed successfully in {work_dir}.")
if __name__ == "__main__":
    main()






