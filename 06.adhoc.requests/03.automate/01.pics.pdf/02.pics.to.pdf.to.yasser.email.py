# %%
import os
from PIL import Image
from reportlab.pdfgen import canvas

def images_to_pdf(input_folder, output_pdf):
    # Create a PDF file
    pdf = canvas.Canvas(output_pdf)
    
    # Add cover page
    cover_title = "Progress Pictures From Site"
    
    # Set page size to landscape
    pdf.setPageSize((pdf._pagesize[1], pdf._pagesize[0]))
    
    # Get the width and height of the canvas
    width, height = pdf._pagesize
    
    # Increase font size for the cover title
    pdf.setFont("Helvetica", 24)
    
    # Center the text on the cover page
    pdf.drawCentredString(width / 2, height / 2, cover_title)
    pdf.showPage()
    
    # Get a list of all files in the input folder
    files = os.listdir(input_folder)
    
    # Filter only image files
    image_files = [file for file in files if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    
    # Sort image files alphabetically
    image_files.sort()
    
    for image_file in image_files:
        # Get the full path of the image
        image_path = os.path.join(input_folder, image_file)
        
        # Open the image using Pillow
        img = Image.open(image_path)
        
        # Get the dimensions of the image
        img_width, img_height = img.size
        
        # Add a new page to the PDF with the size of the image
        pdf.setPageSize((img_width, img_height))
        pdf.showPage()
        
        # Draw the image on the PDF
        pdf.drawInlineImage(image_path, 0, 0, width=img_width, height=img_height)
    
    # Save the PDF
    pdf.save()

if __name__ == "__main__":
    input_folder = "pics"
    output_pdf = "site_progress_pictures.pdf"
    
    images_to_pdf(input_folder, output_pdf)
    print(f"PDF created successfully: {output_pdf}")


# %%
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import PyPDF2

def send_email_with_pdf(pdf_filename):
    # Set up the email content
    email = MIMEMultipart()
    email['From'] = 'omaressamrme@gmail.com'
    email['To'] = 'yasser.abouzeid@rowad-rme.com'
    email['Subject'] = 'Site Progress Pictures'

    # Add body text (optional)
    email.attach(MIMEText('Please find the site progress pictures attached.'))

    # Attach the PDF file
    with open(pdf_filename, 'rb') as pdf_file:
        pdf_attachment = MIMEApplication(pdf_file.read(), _subtype="pdf")
        pdf_attachment.add_header('Content-Disposition', f'attachment; filename={pdf_filename}')
        email.attach(pdf_attachment)

    # Connect to the SMTP server (Gmail in this case)
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # Use TLS encryption
        # Use the generated App Password instead of your Gmail password
        gmail_app_password = 'krnn bntk gvnv jgak'
        server.login('omaressamrme@gmail.com', gmail_app_password)
        server.send_message(email)

if __name__ == "__main__":
    pdf_filename = "site_progress_pictures.pdf"

    try:
        send_email_with_pdf(pdf_filename)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error: {e}")



