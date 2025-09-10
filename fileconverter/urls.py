# urls.py
from django.urls import path
from . import views

app_name = 'fileconverter'

urlpatterns = [
    path('', views.pdf_tools_home, name='home'),
    path('upload/', views.upload_pdf, name='upload_pdf'),
    path('extract-text/', views.extract_text, name='extract_text'),
    path('split-pdf/', views.split_pdf, name='split_pdf'),
    path('merge-pdfs/', views.merge_pdfs, name='merge_pdfs'),
    path('compress-pdf/', views.compress_pdf, name='compress_pdf'),
    path('add-watermark/', views.add_watermark, name='add_watermark'),
    path('rotate-pages/', views.rotate_pages, name='rotate_pages'),
    path('delete-pages/', views.delete_pages, name='delete_pages'),
    path('extract-pages/', views.extract_pages, name='extract_pages'),
    path('pdf-to-images/', views.pdf_to_images, name='pdf_to_images'),
    path('get-metadata/', views.get_metadata, name='get_metadata'),
    path('pdf-reader/', views.pdf_reader, name='pdf_reader'),
]
