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


