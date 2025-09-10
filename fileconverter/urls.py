from django.urls import path
from . import views

# App namespace for URL reversing (fileconverter app)
app_name = 'fileconverter'

urlpatterns = [
    # Main PDF Tools Dashboard
    path('/', views.index, name='index'),
    
    # Core PDF Operations
    path('extract-text/', views.extract_text, name='extract_text'),
    path('split-pdf/', views.split_pdf, name='split_pdf'),
    path('merge-pdfs/', views.merge_pdfs, name='merge_pdfs'),
    path('compress-pdf/', views.compress_pdf, name='compress_pdf'),
    path('add-watermark/', views.add_watermark, name='add_watermark'),
    path('rotate-pages/', views.rotate_pages, name='rotate_pages'),
    path('delete-pages/', views.delete_pages, name='delete_pages'),
    path('extract-pages/', views.extract_pages, name='extract_pages'),
    path('view-metadata/', views.view_metadata, name='view_metadata'),
    path('convert-to-images/', views.convert_to_images, name='convert_to_images'),
    path('protect-pdf/', views.protect_pdf, name='protect_pdf'),
    path('remove-protection/', views.remove_protection, name='remove_protection'),
    
    # AJAX API endpoints for dynamic web interactions
    path('ajax/extract-text/', views.extract_text, name='ajax_extract_text'),
    path('ajax/split-pdf/', views.split_pdf, name='ajax_split_pdf'),
    path('ajax/merge-pdfs/', views.merge_pdfs, name='ajax_merge_pdfs'),
    path('ajax/compress-pdf/', views.compress_pdf, name='ajax_compress_pdf'),
    path('ajax/add-watermark/', views.add_watermark, name='ajax_add_watermark'),
    path('ajax/rotate-pages/', views.rotate_pages, name='ajax_rotate_pages'),
    path('ajax/delete-pages/', views.delete_pages, name='ajax_delete_pages'),
    path('ajax/extract-pages/', views.extract_pages, name='ajax_extract_pages'),
    path('ajax/view-metadata/', views.view_metadata, name='ajax_view_metadata'),
    path('ajax/convert-to-images/', views.convert_to_images, name='ajax_convert_to_images'),
    path('ajax/protect-pdf/', views.protect_pdf, name='ajax_protect_pdf'),
    path('ajax/remove-protection/', views.remove_protection, name='ajax_remove_protection'),
]

# URL Patterns Explanation:
# 
# Based on your main project URLs: path('pdftools',include('fileconverter.urls'))
# All URLs will be accessible as:
# 
# /pdftools/ → Main PDF Tools page (views.index)
# /pdftools/extract-text/ → Extract text from PDF (views.extract_text)
# /pdftools/split-pdf/ → Split PDF into pages (views.split_pdf)  
# /pdftools/merge-pdfs/ → Merge multiple PDFs (views.merge_pdfs)
# /pdftools/compress-pdf/ → Compress PDF file (views.compress_pdf)
# /pdftools/add-watermark/ → Add watermark to PDF (views.add_watermark)
# /pdftools/rotate-pages/ → Rotate PDF pages (views.rotate_pages)
# /pdftools/delete-pages/ → Delete PDF pages (views.delete_pages)
# /pdftools/extract-pages/ → Extract specific pages (views.extract_pages)
# /pdftools/view-metadata/ → View PDF metadata (views.view_metadata)
# /pdftools/convert-to-images/ → Convert PDF to images (views.convert_to_images)
# /pdftools/protect-pdf/ → Add password protection (views.protect_pdf)
# /pdftools/remove-protection/ → Remove password (views.remove_protection)
# 
# AJAX endpoints (for JavaScript calls):
# /pdftools/ajax/extract-text/ → AJAX text extraction
# /pdftools/ajax/merge-pdfs/ → AJAX PDF merging
# ... and so on for all operations
# 
# Template Usage Examples:
# {% url 'fileconverter:index' %} → /pdftools/
# {% url 'fileconverter:extract_text' %} → /pdftools/extract-text/
# {% url 'fileconverter:ajax_merge_pdfs' %} → /pdftools/ajax/merge-pdfs/
# 
# Form Example:
# <form method="post" action="{% url 'fileconverter:compress_pdf' %}" enctype="multipart/form-data">
#     {% csrf_token %}
#     <input type="file" name="pdf_file" accept=".pdf">
#     <button type="submit">Compress PDF</button>
# </form>
# 
# JavaScript AJAX Example:
# const extractUrl = "{% url 'fileconverter:ajax_extract_text' %}";
# fetch(extractUrl, {
#     method: 'POST',
#     body: formData,
#     headers: {'X-CSRFToken': getCookie('csrftoken')}
# })
