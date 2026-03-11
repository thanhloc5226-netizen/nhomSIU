from django.shortcuts import render
from portfolio.models import *

# Create your views here.
def portfolio(request):
    category = Category.objects.all()
    portfolio = Portfolio.objects.all()
    context = {
        'category': category,
        'portfolio': portfolio,
    }
    return render(request, 'portfolio/portfolio.html',context)