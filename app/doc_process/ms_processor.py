import subprocess
import tempfile
import os
import PyPDF2
from io import BytesIO
from werkzeug.utils import secure_filename

def get_page_count(docx_file, pdf_files, organisation, filename, copies, orientation):
    # Create a temporary directory to store the converted PDF
    with tempfile.TemporaryDirectory() as tempdir:
        # Save the uploaded file (FileStorage) to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_docx:
            docx_file.save(temp_docx)
            docx_path = temp_docx.name
        
        try:
            # Convert the DOCX file to PDF using LibreOffice, outputting to the temp directory
            subprocess.run([
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                docx_path,
                "--outdir",
                tempdir
            ], check=True)

            # Get the path of the converted PDF file
            pdf_file = os.path.join(tempdir, os.path.basename(docx_path).rsplit(".", 1)[0] + ".pdf")

            # Open the converted PDF file to get the page count
            with open(pdf_file, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)

                # Calculate the total pages based on the number of copies
                total_pages = num_pages * copies

                # Read the binary PDF data
                pdf_data = file.read()

                # Append to the pdf_files list
                pdf_files.append({
                    'organisation': organisation,
                    'filename': filename,
                    'pdf_data': pdf_data,
                    'num_pages': total_pages,
                    'copies': copies,
                    'orientation': orientation
                })

        finally:
            # Clean up the temporary DOCX file
            os.remove(docx_path)

    return total_pages,pdf_data


def get_page_count2(docx_file):
    # Create a temporary directory to store the converted PDF
    with tempfile.TemporaryDirectory() as tempdir:
        # Save the uploaded file (FileStorage) to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_docx:
            docx_file.save(temp_docx)
            docx_path = temp_docx.name
        
        
        try:
            # Convert the DOCX file to PDF using LibreOffice, outputting to the temp directory
            subprocess.run([
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                docx_path,
                "--outdir",
                tempdir
            ], check=True)

            # Get the path of the converted PDF file
            pdf_file = os.path.join(tempdir, os.path.basename(docx_path).rsplit(".", 1)[0] + ".pdf")

            # Open the converted PDF file to get the page count
            with open(pdf_file, "rb") as file:
                pdf_data = file.read()  
                pdf_file = BytesIO(pdf_data) 
                reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(reader.pages)

                #pdf_reader = PyPDF2.PdfReader(file)
                #num_pages = len(pdf_reader.pages)

                # Calculate the total pages based on the number of copies

                # Read the binary PDF data
                #pdf_data = file.read()


        finally:
            # Clean up the temporary DOCX file
            os.remove(docx_path)
 
    return num_pages,pdf_data,file


if __name__ == "__main__":
    # Example usage
    #docx_file_path = r"Rajashri_Report.docx"
    from werkzeug.datastructures import FileStorage

# Example of a FileStorage object (from Flask request.files)
    file = FileStorage(filename="report.docx", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    pages,_ = get_page_count2(file)
    print(f"Page count: {pages}")
