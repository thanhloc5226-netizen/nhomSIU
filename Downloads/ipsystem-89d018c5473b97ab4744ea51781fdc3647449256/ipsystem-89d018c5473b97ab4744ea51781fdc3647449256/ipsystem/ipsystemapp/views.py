from django.shortcuts import render, redirect
from portfolio.models import *

def home(request):
    category = Category.objects.all()
    context = {
        'category': category,
    }
    return render(request, 'ipsystemapp/home.html',context)












