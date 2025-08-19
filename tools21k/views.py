from django.http import HttpResponse
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')
def help(request):
    return render(request, 'help.html')

def privacypolicy(request):
    return render(request, 'pp.html')

def termsandconditions(request):
    return render(request, 'tc.html')
def about(request):
    return render(request, 'about.html')

def blog(request):
    return render(request, 'blog.html')

def age(request):
    return render(request, 'age.html')

def time(request):
    return render(request, 'time.html')
def interest(request):
    return render(request, 'interest.html')

    
from django.shortcuts import render

def custom_page_not_found(request, exception):
    return render(request, '404.html', status=404)

handler404 = custom_page_not_found
