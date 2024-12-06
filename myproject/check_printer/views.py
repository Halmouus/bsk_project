from django.shortcuts import render
from django.views.generic import TemplateView

class CheckPrinterView(TemplateView):
    template_name = "check_printer/index.html"
