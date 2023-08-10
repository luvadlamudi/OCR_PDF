import streamlit as st
import os
import time
import calendar
import shutil
from pathlib import Path
from PyPDF2 import PdfMerger
import base64
from io import BytesIO
import threading
from streamlit_lottie import st_lottie 
from PIL import Image
from pdf2image import convert_from_path
import pytesseract
import requests

# Set Streamlit page configuration
st.set_page_config(page_title="OCR PDF", page_icon=":pdf:", initial_sidebar_state="expanded")

# Function to load Lottie animation from URL
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Load Lottie animation
lottie_ocr = load_lottieurl("https://assets8.lottiefiles.com/packages/lf20_ow1gekva.json")

# Create columns layout
left_column, right_column = st.columns([1, 0.5])

# Display the title in the left column
with left_column:
    st.write("##")
    st.markdown("# OCR PDF", unsafe_allow_html=True)

# Display the Lottie animation in the right column
with right_column:
    st.write("##")
    st_lottie(lottie_ocr, height=100, width=200)

# OCR PDF function  
# OCR PDF function  
def ocr_pdf(pdf_path: str):

    poppler_path = r"C:\Program Files\poppler-23.05.0\Library\bin"
    file_name, f = os.path.splitext(os.path.basename(pdf_path))
    folder = str(int(calendar.timegm(time.gmtime()))) + '_' + file_name
    combined = os.path.join(folder, file_name)
    file_extension = f.lower()

    if not os.path.exists(folder):
        os.makedirs(folder)

    if file_name.endswith("-ocr"):
        # Delete the temporary folder and its contents
        shutil.rmtree(folder)
        return None

    # Image to PDF
    elif file_extension == '.png' or file_extension == '.jpg' or file_extension == '.jpeg':
        image = Image.open(pdf_path)
        image_converted = image.convert('RGB')
        pdf_path = os.path.join(folder, f"{file_name}.pdf")
        image_converted.save(pdf_path)
        file_extension = '.pdf'

    # PDF to OCR PDF
    if file_extension == '.pdf':
        try:
            images = convert_from_path(pdf_path, poppler_path=poppler_path, dpi=150)
        except Exception as e:
            # Reset on ERROR
            print("Error occurred while converting PDF to images:", e)
            # Delete the temporary folder and its contents
            shutil.rmtree(folder)
            os.remove(pdf_path)
            return

        # Temporary file list 
        ocr_pdf_paths = []

        for i, image in enumerate(images):
            image_name = f'{file_name}-{i+1:04d}.png'
            image_path = os.path.join(folder, image_name)
            image.save(image_path, 'PNG')

            pdf = pytesseract.image_to_pdf_or_hocr(image, extension='pdf')
            pdf_path = os.path.join(folder, f'{file_name}-{i+1:04d}.pdf')

            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(pdf)

            # Append the absolute OCR'd PDF path to the temporary list
            absolute_pdf_path = os.path.abspath(pdf_path)
            ocr_pdf_paths.append(absolute_pdf_path)

        # Merge OCR PDF's
        merger = PdfMerger()
        for pdf in ocr_pdf_paths:
            if pdf.endswith('.pdf'):
                merger.append(pdf)  # Use the absolute path

        output_path = os.path.join(os.path.dirname(pdf_path), file_name + '-ocr.pdf')
        merger.write(output_path)
        merger.close()

        # Delete the temporary folder and its contents
        shutil.rmtree(folder)

        return output_path

# Function to generate download link for a file
def get_download_link(file_path, file_name):
    with open(file_path, 'rb') as f:
        base64_encoded = base64.b64encode(f.read()).decode()
    download_link = f'<a href="data:application/octet-stream;base64,{base64_encoded}" download="{file_name}">Download {file_name}</a>'
    return download_link


# Streamlit
def main():
    # Allows it to accept multiple PDF files
    st.write("---")
    st.write("##")
    st.write(" ##### Upload PDFs")
    uploaded_files = st.file_uploader(" ", type='pdf', accept_multiple_files=True)

    # If there are uploaded files ...
    if uploaded_files:
        ocr_files = []
        # Display progress bar while OCR process is running
        progress_text = "Performing OCR... Please wait."
        my_bar = st.progress(0)
        for i, uploaded_file in enumerate(uploaded_files):
            # Read the contents of the uploaded file
            file_contents = uploaded_file.read()

            # Generate a unique filename for each uploaded file
            file_name = f'{str(int(calendar.timegm(time.gmtime())))}_{uploaded_file.name}'

            # Check if the file already has the "-ocr" suffix
            if file_name.endswith('-ocr.pdf'):
                continue

            # Add the "-ocr" suffix to the file name
            file_name_ocr = file_name.replace('.pdf', '-ocr.pdf')

            # Write the file contents to a temporary location
            temp_path = os.path.join(Path.home(), file_name)
            with open(temp_path, 'wb') as f:
                f.write(file_contents)

            # Perform OCR on the uploaded PDF file
            ocr_file_path = ocr_pdf(temp_path)
            if ocr_file_path:
                ocr_files.append((ocr_file_path, file_name_ocr))

            # Delete the temporary file
            os.remove(temp_path)

            # Update progress bar
            progress_percent = int((i + 1) / len(uploaded_files) * 100)
            my_bar.progress(progress_percent)

        # Display the download buttons for the OCR'd PDF files
        for ocr_file_path, file_name in ocr_files:
            if os.path.exists(ocr_file_path):
                download_link = get_download_link(ocr_file_path, file_name)
                st.markdown(download_link, unsafe_allow_html=True)

        # Button to download all OCR'd PDFs
        if len(ocr_files) > 1:
            download_all(ocr_files)  # Call the function directly

# Function to merge OCR'd PDF files
def merge_pdf_files(ocr_files):
    merger = PdfMerger()

    # Merge all the OCR'd PDF files into one
    for ocr_file_path, _ in ocr_files:
        merger.append(ocr_file_path)

    # Generate a unique filename for the merged PDF
    merged_file_name = 'All_OCR_PDFs.pdf'
    merged_file_path = os.path.join(Path.home(), merged_file_name)

    # Save the merged PDF
    merger.write(merged_file_path)
    merger.close()

    return merged_file_path

# Function to download all OCR'd PDFs
def download_all(ocr_files):
    merged_file_path = merge_pdf_files(ocr_files)
    merged_file_name = 'All_OCR_PDFs.pdf'
    download_all_link = get_download_link(merged_file_path, merged_file_name)
    st.markdown(f'<a href="{download_all_link}" download="{merged_file_name}"><button>Download All OCR\'d PDFs</button></a>',
                unsafe_allow_html=True)
if __name__ == '__main__':
    main()
