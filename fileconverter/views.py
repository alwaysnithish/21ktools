import os
import io
import json
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import PyPDF2
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import zipfile


class PDFToolsView:
    """Main PDF Tools View Class"""
    
    @staticmethod
    def index(request):
        """Main PDF tools page"""
        return render(request, 'pdftools.html')
    
    @staticmethod
    def extract_text(request):
        """Extract text from PDF"""
        if request.method == 'POST':
            try:
                pdf_file = request.FILES.get('pdf_file')
                if not pdf_file:
                    return JsonResponse({'error': 'No PDF file provided'}, status=400)
                
                # Read PDF and extract text
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                extracted_text = ""
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    extracted_text += f"--- Page {page_num} ---\n{text}\n\n"
                
                # Create text file
                text_filename = f"extracted_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                response = HttpResponse(extracted_text, content_type='text/plain')
                response['Content-Disposition'] = f'attachment; filename="{text_filename}"'
                return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error extracting text: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')
    
    @staticmethod
    def split_pdf(request):
        """Split PDF into pages or ranges"""
        if request.method == 'POST':
            try:
                pdf_file = request.FILES.get('pdf_file')
                split_type = request.POST.get('split_type', 'pages')  # 'pages' or 'ranges'
                page_ranges = request.POST.get('page_ranges', '')
                
                if not pdf_file:
                    return JsonResponse({'error': 'No PDF file provided'}, status=400)
                
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                total_pages = len(pdf_reader.pages)
                
                # Create ZIP file for multiple PDFs
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    if split_type == 'pages':
                        # Split into individual pages
                        for page_num in range(total_pages):
                            pdf_writer = PyPDF2.PdfWriter()
                            pdf_writer.add_page(pdf_reader.pages[page_num])
                            
                            page_buffer = io.BytesIO()
                            pdf_writer.write(page_buffer)
                            page_buffer.seek(0)
                            
                            filename = f"page_{page_num + 1}.pdf"
                            zip_file.writestr(filename, page_buffer.getvalue())
                    
                    else:  # split by ranges
                        ranges = page_ranges.split(',')
                        for i, range_str in enumerate(ranges):
                            range_str = range_str.strip()
                            if '-' in range_str:
                                start, end = map(int, range_str.split('-'))
                            else:
                                start = end = int(range_str)
                            
                            pdf_writer = PyPDF2.PdfWriter()
                            for page_num in range(start - 1, min(end, total_pages)):
                                pdf_writer.add_page(pdf_reader.pages[page_num])
                            
                            range_buffer = io.BytesIO()
                            pdf_writer.write(range_buffer)
                            range_buffer.seek(0)
                            
                            filename = f"pages_{start}_to_{end}.pdf"
                            zip_file.writestr(filename, range_buffer.getvalue())
                
                zip_buffer.seek(0)
                
                response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="split_pdfs.zip"'
                return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error splitting PDF: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')
    
    @staticmethod
    def merge_pdfs(request):
        """Merge multiple PDFs into one"""
        if request.method == 'POST':
            try:
                pdf_files = request.FILES.getlist('pdf_files')
                
                if len(pdf_files) < 2:
                    return JsonResponse({'error': 'At least 2 PDF files required for merging'}, status=400)
                
                pdf_writer = PyPDF2.PdfWriter()
                
                for pdf_file in pdf_files:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    for page in pdf_reader.pages:
                        pdf_writer.add_page(page)
                
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                output_buffer.seek(0)
                
                response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="merged_document.pdf"'
                return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error merging PDFs: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')
    
    @staticmethod
    def compress_pdf(request):
        """Compress PDF to reduce file size"""
        if request.method == 'POST':
            try:
                pdf_file = request.FILES.get('pdf_file')
                quality = int(request.POST.get('quality', 75))  # 1-100
                
                if not pdf_file:
                    return JsonResponse({'error': 'No PDF file provided'}, status=400)
                
                # Use PyMuPDF for compression
                pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
                
                # Compress images and reduce quality
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)
                    image_list = page.get_images()
                    
                    for img_index, img in enumerate(image_list):
                        xref = img[0]
                        pix = fitz.Pixmap(pdf_document, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            # Convert to PIL Image for compression
                            img_data = pix.tobytes("png")
                            pil_img = Image.open(io.BytesIO(img_data))
                            
                            # Compress image
                            compressed_buffer = io.BytesIO()
                            pil_img.save(compressed_buffer, format='JPEG', quality=quality, optimize=True)
                            compressed_buffer.seek(0)
                            
                            # Replace image in PDF
                            pdf_document.update_stream(xref, compressed_buffer.getvalue())
                        
                        pix = None
                
                # Save compressed PDF
                output_buffer = io.BytesIO()
                pdf_document.save(output_buffer, garbage=4, deflate=True, clean=True)
                output_buffer.seek(0)
                pdf_document.close()
                
                response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="compressed_document.pdf"'
                return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error compressing PDF: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')
    
    @staticmethod
    def add_watermark(request):
        """Add watermark to PDF"""
        if request.method == 'POST':
            try:
                pdf_file = request.FILES.get('pdf_file')
                watermark_text = request.POST.get('watermark_text', 'WATERMARK')
                opacity = float(request.POST.get('opacity', 0.3))
                position = request.POST.get('position', 'center')  # center, top-left, top-right, etc.
                font_size = int(request.POST.get('font_size', 50))
                
                if not pdf_file:
                    return JsonResponse({'error': 'No PDF file provided'}, status=400)
                
                # Create watermark PDF
                watermark_buffer = io.BytesIO()
                c = canvas.Canvas(watermark_buffer, pagesize=letter)
                
                # Set transparency and text properties
                c.setFillColorRGB(0.5, 0.5, 0.5, opacity)
                c.setFont("Helvetica-Bold", font_size)
                
                # Position watermark
                width, height = letter
                if position == 'center':
                    x, y = width/2, height/2
                elif position == 'top-left':
                    x, y = 50, height - 50
                elif position == 'top-right':
                    x, y = width - 200, height - 50
                elif position == 'bottom-left':
                    x, y = 50, 50
                else:  # bottom-right
                    x, y = width - 200, 50
                
                # Draw watermark
                c.saveState()
                c.translate(x, y)
                c.rotate(45)  # Diagonal watermark
                c.drawCentredText(0, 0, watermark_text)
                c.restoreState()
                c.save()
                
                # Apply watermark to PDF
                watermark_buffer.seek(0)
                watermark_pdf = PyPDF2.PdfReader(watermark_buffer)
                watermark_page = watermark_pdf.pages[0]
                
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                pdf_writer = PyPDF2.PdfWriter()
                
                for page in pdf_reader.pages:
                    page.merge_page(watermark_page)
                    pdf_writer.add_page(page)
                
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                output_buffer.seek(0)
                
                response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="watermarked_document.pdf"'
                return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error adding watermark: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')
    
    @staticmethod
    def rotate_pages(request):
        """Rotate PDF pages"""
        if request.method == 'POST':
            try:
                pdf_file = request.FILES.get('pdf_file')
                rotation = int(request.POST.get('rotation', 90))  # 90, 180, 270
                pages_to_rotate = request.POST.get('pages', 'all')  # 'all' or comma-separated page numbers
                
                if not pdf_file:
                    return JsonResponse({'error': 'No PDF file provided'}, status=400)
                
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                pdf_writer = PyPDF2.PdfWriter()
                
                total_pages = len(pdf_reader.pages)
                
                if pages_to_rotate == 'all':
                    pages_list = list(range(total_pages))
                else:
                    pages_list = [int(p.strip()) - 1 for p in pages_to_rotate.split(',') if p.strip().isdigit()]
                
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    if page_num in pages_list:
                        page = page.rotate(rotation)
                    pdf_writer.add_page(page)
                
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                output_buffer.seek(0)
                
                response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="rotated_document.pdf"'
                return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error rotating pages: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')
    
    @staticmethod
    def delete_pages(request):
        """Delete specific pages from PDF"""
        if request.method == 'POST':
            try:
                pdf_file = request.FILES.get('pdf_file')
                pages_to_delete = request.POST.get('pages_to_delete', '')
                
                if not pdf_file:
                    return JsonResponse({'error': 'No PDF file provided'}, status=400)
                
                if not pages_to_delete:
                    return JsonResponse({'error': 'No pages specified for deletion'}, status=400)
                
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                pdf_writer = PyPDF2.PdfWriter()
                
                total_pages = len(pdf_reader.pages)
                delete_list = [int(p.strip()) - 1 for p in pages_to_delete.split(',') if p.strip().isdigit()]
                
                for page_num in range(total_pages):
                    if page_num not in delete_list:
                        pdf_writer.add_page(pdf_reader.pages[page_num])
                
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                output_buffer.seek(0)
                
                response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="document_with_deleted_pages.pdf"'
                return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error deleting pages: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')
    
    @staticmethod
    def extract_pages(request):
        """Extract specific pages into new PDF"""
        if request.method == 'POST':
            try:
                pdf_file = request.FILES.get('pdf_file')
                pages_to_extract = request.POST.get('pages_to_extract', '')
                
                if not pdf_file:
                    return JsonResponse({'error': 'No PDF file provided'}, status=400)
                
                if not pages_to_extract:
                    return JsonResponse({'error': 'No pages specified for extraction'}, status=400)
                
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                pdf_writer = PyPDF2.PdfWriter()
                
                extract_list = []
                for page_range in pages_to_extract.split(','):
                    page_range = page_range.strip()
                    if '-' in page_range:
                        start, end = map(int, page_range.split('-'))
                        extract_list.extend(range(start - 1, end))
                    else:
                        extract_list.append(int(page_range) - 1)
                
                for page_num in sorted(set(extract_list)):
                    if 0 <= page_num < len(pdf_reader.pages):
                        pdf_writer.add_page(pdf_reader.pages[page_num])
                
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                output_buffer.seek(0)
                
                response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="extracted_pages.pdf"'
                return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error extracting pages: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')
    
    @staticmethod
    def view_metadata(request):
        """View PDF metadata"""
        if request.method == 'POST':
            try:
                pdf_file = request.FILES.get('pdf_file')
                
                if not pdf_file:
                    return JsonResponse({'error': 'No PDF file provided'}, status=400)
                
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                metadata = {
                    'total_pages': len(pdf_reader.pages),
                    'file_size': f"{pdf_file.size / (1024*1024):.2f} MB",
                    'encrypted': pdf_reader.is_encrypted,
                }
                
                # Get document info
                if pdf_reader.metadata:
                    doc_info = pdf_reader.metadata
                    metadata.update({
                        'title': doc_info.get('/Title', 'N/A'),
                        'author': doc_info.get('/Author', 'N/A'),
                        'subject': doc_info.get('/Subject', 'N/A'),
                        'creator': doc_info.get('/Creator', 'N/A'),
                        'producer': doc_info.get('/Producer', 'N/A'),
                        'creation_date': str(doc_info.get('/CreationDate', 'N/A')),
                        'modification_date': str(doc_info.get('/ModDate', 'N/A')),
                    })
                
                return JsonResponse({'metadata': metadata})
                
            except Exception as e:
                return JsonResponse({'error': f'Error reading metadata: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')
    
    @staticmethod
    def convert_to_images(request):
        """Convert PDF pages to images"""
        if request.method == 'POST':
            try:
                pdf_file = request.FILES.get('pdf_file')
                image_format = request.POST.get('format', 'PNG')  # PNG, JPEG
                dpi = int(request.POST.get('dpi', 150))
                
                if not pdf_file:
                    return JsonResponse({'error': 'No PDF file provided'}, status=400)
                
                pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
                
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    for page_num in range(len(pdf_document)):
                        page = pdf_document.load_page(page_num)
                        
                        # Render page to image
                        mat = fitz.Matrix(dpi/72, dpi/72)
                        pix = page.get_pixmap(matrix=mat)
                        
                        img_data = pix.tobytes(image_format.lower())
                        filename = f"page_{page_num + 1}.{image_format.lower()}"
                        zip_file.writestr(filename, img_data)
                
                pdf_document.close()
                zip_buffer.seek(0)
                
                response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename="pdf_images.zip"'
                return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error converting to images: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')
    
    @staticmethod
    def protect_pdf(request):
        """Add password protection to PDF"""
        if request.method == 'POST':
            try:
                pdf_file = request.FILES.get('pdf_file')
                user_password = request.POST.get('user_password', '')
                owner_password = request.POST.get('owner_password', '')
                
                if not pdf_file:
                    return JsonResponse({'error': 'No PDF file provided'}, status=400)
                
                if not user_password and not owner_password:
                    return JsonResponse({'error': 'At least one password must be provided'}, status=400)
                
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                pdf_writer = PyPDF2.PdfWriter()
                
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                
                # Encrypt the PDF
                pdf_writer.encrypt(
                    user_password=user_password or owner_password,
                    owner_password=owner_password or user_password
                )
                
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                output_buffer.seek(0)
                
                response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="protected_document.pdf"'
                return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error protecting PDF: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')
    
    @staticmethod
    def remove_protection(request):
        """Remove password protection from PDF"""
        if request.method == 'POST':
            try:
                pdf_file = request.FILES.get('pdf_file')
                password = request.POST.get('password', '')
                
                if not pdf_file:
                    return JsonResponse({'error': 'No PDF file provided'}, status=400)
                
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                if pdf_reader.is_encrypted:
                    if not pdf_reader.decrypt(password):
                        return JsonResponse({'error': 'Incorrect password'}, status=400)
                
                pdf_writer = PyPDF2.PdfWriter()
                
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                
                output_buffer = io.BytesIO()
                pdf_writer.write(output_buffer)
                output_buffer.seek(0)
                
                response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="unprotected_document.pdf"'
                return response
                
            except Exception as e:
                return JsonResponse({'error': f'Error removing protection: {str(e)}'}, status=500)
        
        return render(request, 'pdftools.html')


# URL mapping functions
def index(request):
    return PDFToolsView.index(request)

def extract_text(request):
    return PDFToolsView.extract_text(request)

def split_pdf(request):
    return PDFToolsView.split_pdf(request)

def merge_pdfs(request):
    return PDFToolsView.merge_pdfs(request)

def compress_pdf(request):
    return PDFToolsView.compress_pdf(request)

def add_watermark(request):
    return PDFToolsView.add_watermark(request)

def rotate_pages(request):
    return PDFToolsView.rotate_pages(request)

def delete_pages(request):
    return PDFToolsView.delete_pages(request)

def extract_pages(request):
    return PDFToolsView.extract_pages(request)

def view_metadata(request):
    return PDFToolsView.view_metadata(request)

def convert_to_images(request):
    return PDFToolsView.convert_to_images(request)

def protect_pdf(request):
    return PDFToolsView.protect_pdf(request)

def remove_protection(request):
    return PDFToolsView.remove_protection(request)
