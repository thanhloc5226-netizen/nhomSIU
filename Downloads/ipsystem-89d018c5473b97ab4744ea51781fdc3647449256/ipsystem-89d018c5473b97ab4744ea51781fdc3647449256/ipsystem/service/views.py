from django.shortcuts import render
from portfolio.models import *
# Create your views here.
def service(request):
    category = Category.objects.all()
    context = {
        'category': category,
    }
    return render(request, 'service/service.html',context)