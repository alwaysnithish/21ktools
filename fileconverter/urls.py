from django.urls import path
from . import views

app_name = 'fileconverter'

urlpatterns = [
    # Home page
    path('', views.pdf_tools_home, name='home'),
    
    # File upload and basic operations
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('extract-text/', views.extract_text, name='extract_text'),
    path('extract-images/', views.extract_images, name='extract_images'),
    path('metadata/', views.get_pdf_metadata, name='get_pdf_metadata'),
    
    # PDF manipulation operations
    path('split/', views.split_pdf, name='split_pdf'),
    path('merge/', views.merge_pdfs, name='merge_pdfs'),
    path('compress/', views.compress_pdf, name='compress_pdf'),
    path('optimize/', views.optimize_pdf, name='optimize_pdf'),
    
    # Page operations
    path('rotate-pages/', views.rotate_pages, name='rotate_pages'),
    path('delete-pages/', views.delete_pages, name='delete_pages'),
    path('extract-pages/', views.extract_pages, name='extract_pages'),
    path('rearrange-pages/', views.rearrange_pages, name='rearrange_pages'),
    
    # Security operations
    path('add-password/', views.add_password, name='add_password'),
    path('remove-password/', views.remove_password, name='remove_password'),
    path('add-watermark/', views.add_watermark, name='add_watermark'),
    
    # Conversion operations
    path('convert-to-images/', views.convert_to_images, name='convert_to_images'),
    path('images-to-pdf/', views.images_to_pdf, name='images_to_pdf'),
    path('html-to-pdf/', views.html_to_pdf, name='html_to_pdf'),
    path('pdf-to-word/', views.pdf_to_word, name='pdf_to_word'),
    
    # Batch operations
    path('batch-process/', views.batch_process, name='batch_process'),
    
    # Download operations
    path('download/<str:file_type>/', views.download_file, name='download_file'),
    path('download-zip/', views.download_zip, name='download_zip'),
    
    # Utility operations
    path('cleanup/', views.cleanup_temp_files, name='cleanup_temp_files'),
]
