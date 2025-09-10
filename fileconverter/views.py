# views.py
import os
import json
import uuid
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import PyPDF2
from io import BytesIO
import zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image
import tempfile

# Create a directory for temporary files
TEMP_DIR = os.path.join(settings.BASE_DIR, 'temp_files')
os.makedirs(TEMP_DIR, exist_ok=True)

def pdf_tools_home(request):
    """Render the main PDF tools page"""
    return render(request, 'pdftools.html')

@csrf_exempt
@require_http_methods(["POST"])
def upload_pdf(request):
    """Handle PDF file upload"""
    try:
        if 'pdf_file' not in request.FILES:
            return JsonResponse({'error': 'No PDF file uploaded'}, status=400)
        
        pdf_file = request.FILES['pdf_file']
        
        if not pdf_file.name.lower().endswith('.pdf'):
            return JsonResponse({'error': 'Please upload a valid PDF file'}, status=400)
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_name = f"{file_id}_{pdf_file.name}"
        file_path = os.path.join(TEMP_DIR, file_name)
        
        # Save the file
        with open(file_path, 'wb+') as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)
        
        # Get PDF info
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)
                
                # Extract metadata
                metadata = {}
                if pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', 'N/A'),
                        'author': pdf_reader.metadata.get('/Author', 'N/A'),
                        'creator': pdf_reader.metadata.get('/Creator', 'N/A'),
                        'producer': pdf_reader.metadata.get('/Producer', 'N/A'),
                        'subject': pdf_reader.metadata.get('/Subject', 'N/A'),
                    }
                
                info = {
                    'pages': num_pages,
                    'size': os.path.getsize(file_path),
                    **metadata
                }
        except Exception as e:
            return JsonResponse({'error': f'Error reading PDF: {str(e)}'}, status=500)
        
        return JsonResponse({
            'success': True,
            'file_id': file_id,
            'file_name': pdf_file.name,
            'info': info
        })
    
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def extract_text(request):
    """Extract text from PDF"""
    try:
        file_id = request.POST.get('file_id')
        if not file_id:
            return JsonResponse({'error': 'File ID missing'}, status=400)
        
        # Find the file
        file_path = find_file_by_id(file_id)
        if not file_path:
            return JsonResponse({'error': 'File not found'}, status=404)
        
        # Extract text from PDF
        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                for i, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += f"--- Page {i+1} ---\n{page_text}\n\n"
                
                return JsonResponse({
                    'success': True,
                    'text': text,
                    'page_count': len(pdf_reader.pages)
                })
        except Exception as e:
            return JsonResponse({'error': f'Error extracting text: {str(e)}'}, status=500)
    
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def split_pdf(request):
    """Split PDF into individual pages"""
    try:
        file_id = request.POST.get('file_id')
        split_type = request.POST.get('split_type', 'pages')
        page_ranges = request.POST.get('page_ranges', '')
        
        if not file_id:
            return JsonResponse({'error': 'File ID missing'}, status=400)
        
        # Find the file
        file_path = find_file_by_id(file_id)
        if not file_path:
            return JsonResponse({'error': 'File not found'}, status=404)
        
        # Create a zip file for the split pages
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
                
                if split_type == 'pages':
                    # Split into individual pages
                    for i in range(total_pages):
                        pdf_writer = PyPDF2.PdfWriter()
                        pdf_writer.add_page(pdf_reader.pages[i])
                        
                        page_buffer = BytesIO()
                        pdf_writer.write(page_buffer)
                        
                        zip_file.writestr(f'page_{i+1}.pdf', page_buffer.getvalue())
                
                elif split_type == 'ranges' and page_ranges:
                    # Split by page ranges
                    ranges = parse_page_ranges(page_ranges, total_pages)
                    for range_idx, (start, end) in enumerate(ranges):
                        pdf_writer = PyPDF2.PdfWriter()
                        for i in range(start-1, end):
                            pdf_writer.add_page(pdf_reader.pages[i])
                        
                        page_buffer = BytesIO()
                        pdf_writer.write(page_buffer)
                        
                        zip_file.writestr(f'pages_{start}-{end}.pdf', page_buffer.getvalue())
        
        # Prepare response with zip file
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="split_pages.zip"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def merge_pdfs(request):
    """Merge multiple PDF files"""
    try:
        if 'pdf_files' not in request.FILES:
            return JsonResponse({'error': 'No PDF files uploaded'}, status=400)
        
        pdf_files = request.FILES.getlist('pdf_files')
        
        if len(pdf_files) < 2:
            return JsonResponse({'error': 'At least 2 PDF files required for merging'}, status=400)
        
        pdf_writer = PyPDF2.PdfWriter()
        
        # Process each PDF file
        for pdf_file in pdf_files:
            if pdf_file.name.lower().endswith('.pdf'):
                # Read the PDF file
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
        
        # Write the merged PDF to a buffer
        merged_buffer = BytesIO()
        pdf_writer.write(merged_buffer)
        merged_buffer.seek(0)
        
        # Prepare response with merged PDF
        response = HttpResponse(merged_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="merged_document.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def compress_pdf(request):
    """Compress PDF file"""
    try:
        file_id = request.POST.get('file_id')
        if not file_id:
            return JsonResponse({'error': 'File ID missing'}, status=400)
        
        # Find the file
        file_path = find_file_by_id(file_id)
        if not file_path:
            return JsonResponse({'error': 'File not found'}, status=404)
        
        # For basic compression, we'll just rewrite the PDF
        # In a real implementation, you might use more advanced compression techniques
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            pdf_writer = PyPDF2.PdfWriter()
            
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # Write to buffer
            compressed_buffer = BytesIO()
            pdf_writer.write(compressed_buffer)
            compressed_buffer.seek(0)
        
        # Prepare response with compressed PDF
        response = HttpResponse(compressed_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="compressed_document.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_watermark(request):
    """Add watermark to PDF"""
    try:
        file_id = request.POST.get('file_id')
        watermark_text = request.POST.get('watermark_text', 'WATERMARK')
        
        if not file_id:
            return JsonResponse({'error': 'File ID missing'}, status=400)
        
        # Find the file
        file_path = find_file_by_id(file_id)
        if not file_path:
            return JsonResponse({'error': 'File not found'}, status=404)
        
        # Create a watermark PDF
        watermark_buffer = BytesIO()
        c = canvas.Canvas(watermark_buffer, pagesize=letter)
        c.setFont("Helvetica", 40)
        c.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.3)
        c.rotate(45)
        c.drawString(250, 100, watermark_text)
        c.save()
        
        watermark_buffer.seek(0)
        watermark_reader = PyPDF2.PdfReader(watermark_buffer)
        watermark_page = watermark_reader.pages[0]
        
        # Apply watermark to each page
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            pdf_writer = PyPDF2.PdfWriter()
            
            for page in pdf_reader.pages:
                # Merge watermark with page
                page.merge_page(watermark_page)
                pdf_writer.add_page(page)
            
            # Write to buffer
            watermarked_buffer = BytesIO()
            pdf_writer.write(watermarked_buffer)
            watermarked_buffer.seek(0)
        
        # Prepare response with watermarked PDF
        response = HttpResponse(watermarked_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="watermarked_document.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def rotate_pages(request):
    """Rotate PDF pages"""
    try:
        file_id = request.POST.get('file_id')
        angle = int(request.POST.get('angle', 90))
        pages = request.POST.get('pages', 'all')
        
        if not file_id:
            return JsonResponse({'error': 'File ID missing'}, status=400)
        
        # Find the file
        file_path = find_file_by_id(file_id)
        if not file_path:
            return JsonResponse({'error': 'File not found'}, status=404)
        
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            pdf_writer = PyPDF2.PdfWriter()
            total_pages = len(pdf_reader.pages)
            
            # Determine which pages to rotate
            if pages == 'all':
                pages_to_rotate = list(range(total_pages))
            else:
                pages_to_rotate = [int(p)-1 for p in pages.split(',') if p.isdigit() and 1 <= int(p) <= total_pages]
            
            for i in range(total_pages):
                page = pdf_reader.pages[i]
                if i in pages_to_rotate:
                    page.rotate(angle)
                pdf_writer.add_page(page)
            
            # Write to buffer
            rotated_buffer = BytesIO()
            pdf_writer.write(rotated_buffer)
            rotated_buffer.seek(0)
        
        # Prepare response with rotated PDF
        response = HttpResponse(rotated_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="rotated_document.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def delete_pages(request):
    """Delete pages from PDF"""
    try:
        file_id = request.POST.get('file_id')
        pages_to_delete = request.POST.get('pages', '')
        
        if not file_id:
            return JsonResponse({'error': 'File ID missing'}, status=400)
        
        if not pages_to_delete:
            return JsonResponse({'error': 'No pages specified for deletion'}, status=400)
        
        # Find the file
        file_path = find_file_by_id(file_id)
        if not file_path:
            return JsonResponse({'error': 'File not found'}, status=404)
        
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            pdf_writer = PyPDF2.PdfWriter()
            total_pages = len(pdf_reader.pages)
            
            # Parse pages to delete
            delete_set = set()
            for p in pages_to_delete.split(','):
                if '-' in p:
                    start, end = map(int, p.split('-'))
                    delete_set.update(range(start-1, end))
                elif p.isdigit():
                    delete_set.add(int(p)-1)
            
            # Add pages that are not in delete_set
            for i in range(total_pages):
                if i not in delete_set:
                    pdf_writer.add_page(pdf_reader.pages[i])
            
            if len(pdf_writer.pages) == 0:
                return JsonResponse({'error': 'Cannot delete all pages'}, status=400)
            
            # Write to buffer
            modified_buffer = BytesIO()
            pdf_writer.write(modified_buffer)
            modified_buffer.seek(0)
        
        # Prepare response with modified PDF
        response = HttpResponse(modified_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="modified_document.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def extract_pages(request):
    """Extract specific pages from PDF"""
    try:
        file_id = request.POST.get('file_id')
        pages_to_extract = request.POST.get('pages', '')
        
        if not file_id:
            return JsonResponse({'error': 'File ID missing'}, status=400)
        
        if not pages_to_extract:
            return JsonResponse({'error': 'No pages specified for extraction'}, status=400)
        
        # Find the file
        file_path = find_file_by_id(file_id)
        if not file_path:
            return JsonResponse({'error': 'File not found'}, status=404)
        
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            pdf_writer = PyPDF2.PdfWriter()
            total_pages = len(pdf_reader.pages)
            
            # Parse pages to extract
            extract_set = set()
            for p in pages_to_extract.split(','):
                if '-' in p:
                    start, end = map(int, p.split('-'))
                    extract_set.update(range(start-1, end))
                elif p.isdigit():
                    extract_set.add(int(p)-1)
            
            # Add pages that are in extract_set
            for i in range(total_pages):
                if i in extract_set:
                    pdf_writer.add_page(pdf_reader.pages[i])
            
            if len(pdf_writer.pages) == 0:
                return JsonResponse({'error': 'No valid pages to extract'}, status=400)
            
            # Write to buffer
            extracted_buffer = BytesIO()
            pdf_writer.write(extracted_buffer)
            extracted_buffer.seek(0)
        
        # Prepare response with extracted PDF
        response = HttpResponse(extracted_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="extracted_pages.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def pdf_to_images(request):
    """Convert PDF pages to images"""
    try:
        file_id = request.POST.get('file_id')
        if not file_id:
            return JsonResponse({'error': 'File ID missing'}, status=400)
        
        # Find the file
        file_path = find_file_by_id(file_id)
        if not file_path:
            return JsonResponse({'error': 'File not found'}, status=404)
        
        # This is a placeholder - in a real implementation, you would use
        # a library like pdf2image or PyMuPDF to convert PDF pages to images
        return JsonResponse({
            'success': True,
            'message': 'PDF to image conversion requires additional libraries like pdf2image or PyMuPDF'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def get_metadata(request):
    """Get PDF metadata"""
    try:
        file_id = request.POST.get('file_id')
        if not file_id:
            return JsonResponse({'error': 'File ID missing'}, status=400)
        
        # Find the file
        file_path = find_file_by_id(file_id)
        if not file_path:
            return JsonResponse({'error': 'File not found'}, status=404)
        
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            metadata = {}
            if pdf_reader.metadata:
                for key, value in pdf_reader.metadata.items():
                    # Remove the leading slash from key names
                    clean_key = key[1:] if key.startswith('/') else key
                    metadata[clean_key] = str(value)
            
            # Add basic info
            metadata['pages'] = len(pdf_reader.pages)
            metadata['encrypted'] = pdf_reader.is_encrypted
            metadata['size'] = os.path.getsize(file_path)
            
            return JsonResponse({
                'success': True,
                'metadata': metadata
            })
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def pdf_reader(request):
    """PDF Reader - Extract text and metadata for reading"""
    try:
        file_id = request.POST.get('file_id')
        if not file_id:
            return JsonResponse({'error': 'File ID missing'}, status=400)
        
        # Find the file
        file_path = find_file_by_id(file_id)
        if not file_path:
            return JsonResponse({'error': 'File not found'}, status=404)
        
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            # Extract text from all pages
            full_text = ""
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                full_text += f"--- Page {i+1} ---\n{page_text}\n\n"
            
            # Extract metadata
            metadata = {}
            if pdf_reader.metadata:
                for key, value in pdf_reader.metadata.items():
                    clean_key = key[1:] if key.startswith('/') else key
                    metadata[clean_key] = str(value)
            
            # Add basic info
            metadata['total_pages'] = len(pdf_reader.pages)
            metadata['encrypted'] = pdf_reader.is_encrypted
            
            return JsonResponse({
                'success': True,
                'text': full_text,
                'metadata': metadata,
                'page_count': len(pdf_reader.pages)
            })
        
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)

def find_file_by_id(file_id):
    """Helper function to find file by ID"""
    for file_name in os.listdir(TEMP_DIR):
        if file_name.startswith(file_id):
            return os.path.join(TEMP_DIR, file_name)
    return None

def parse_page_ranges(range_str, max_pages):
    """Parse page range string like '1-3,5-7' into list of tuples"""
    ranges = []
    for part in range_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            try:
                start = max(1, int(start))
                end = min(max_pages, int(end))
                if start <= end:
                    ranges.append((start, end))
            except ValueError:
                continue
        elif part.isdigit():
            page = int(part)
            if 1 <= page <= max_pages:
                ranges.append((page, page))
    return ranges

# Cleanup function to remove temporary files (can be called periodically)
def cleanup_temp_files():
    """Remove temporary files older than 1 hour"""
    import time
    current_time = time.time()
    for file_name in os.listdir(TEMP_DIR):
        file_path = os.path.join(TEMP_DIR, file_name)
        if os.path.isfile(file_path):
            # Remove files older than 1 hour
            if current_time - os.path.getctime(file_path) > 3600:
                os.remove(file_path)
