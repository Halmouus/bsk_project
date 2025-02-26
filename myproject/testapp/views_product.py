from django import forms
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import AssetAccount, Product
from .forms import ProductForm
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.db.models import ProtectedError
from django.db import models
from django.views.generic.edit import DeleteView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
import traceback
from django.db.models import Q
from decimal import Decimal, DecimalException

# List all Products
class ProductListView(ListView):
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'

    def get_template_names(self):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return ['product/includes/product_table.html']
        return [self.template_name]

    def get_queryset(self):
        queryset = Product.objects.all()
        search = self.request.GET.get('search', '')
        type_filter = self.request.GET.get('type', '')
        vat_filter = self.request.GET.get('vat_rate', '')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(fiscal_label__icontains=search) |
                Q(expense_code__icontains=search)
            )
        
        if type_filter:
            if type_filter == 'asset':
                queryset = queryset.filter(is_asset=True)
            elif type_filter == 'regular':
                queryset = queryset.filter(is_asset=False)
            elif type_filter == 'energy':
                queryset = queryset.filter(is_energy=True)
                
        if vat_filter:
            try:
                vat_rate = Decimal(vat_filter.replace(',', '.'))
                queryset = queryset.filter(vat_rate=vat_rate)
            except (ValueError, DecimalException):
                pass
                
        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search': self.request.GET.get('search', ''),
            'type_filter': self.request.GET.get('type', ''),
            'vat_filter': self.request.GET.get('vat_rate', ''),
            'vat_rates': Product.objects.values_list('vat_rate', flat=True).distinct().order_by('vat_rate')
        })
        return context

# Create a new Product
class ProductCreateView(SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully created."

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response

    def form_invalid(self, form):
        print("\n=== Form Invalid Called ===")
        print(f"Form Errors: {form.errors}")
        print(f"Form Data: {form.cleaned_data}")
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add Bootstrap classes to all fields
        for field in form.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input asset-toggle'
            else:
                field.widget.attrs['class'] = 'form-control'
        return form

# Update an existing Product
class ProductUpdateView(SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully updated."

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        product = self.get_object()
        print("Current VAT rate:", product.vat_rate)  # Debug print
        print("Form VAT rate:", form.initial.get('vat_rate'))  # Debug print
        return form

    def get_initial(self):
        initial = super().get_initial()
        product = self.get_object()
        print("Initial VAT rate:", product.vat_rate)  # Debug print
        initial['vat_rate'] = product.vat_rate
        return initial

# Delete a Product
class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product/product_confirm_delete.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully deleted."

    def get(self, request, *args, **kwargs):
        # Check for references before showing the confirmation page
        self.object = self.get_object()
        if self.object.invoiceproduct_set.exists():
            messages.error(request, f'Cannot delete "{self.object.name}". It is used in {self.object.invoiceproduct_set.count()} invoice(s).')
            return redirect('product-list')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, 'Cannot delete product. It is referenced by one or more invoices.')
            return redirect('product-list')


# AJAX view for creating a new Product
@method_decorator(csrf_exempt, name='dispatch')
class ProductAjaxCreateView(View):
    def post(self, request):
        try:
            name = request.POST.get('name')
            # Check for existing product with same name
            if Product.objects.filter(name__iexact=name).exists():
                return JsonResponse({
                    'error': f'A product with the name "{name}" already exists.'
                }, status=400)

            product = Product.objects.create(
                name=name,
                fiscal_label=request.POST.get('fiscal_label'),
                is_energy=request.POST.get('is_energy') == 'true',
                expense_code=request.POST.get('expense_code'),
                vat_rate=request.POST.get('vat_rate')
            )
            return JsonResponse({
                'message': 'Product created successfully',
                'product_id': str(product.id)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class ProductDetailsView(View):
    def get(self, request, pk):
        try:
            product = get_object_or_404(Product, pk=pk)
            return JsonResponse({
                'expense_code': product.expense_code,
                'vat_rate': str(product.vat_rate)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class AssetAccountListView(ListView):
    model = AssetAccount
    template_name = 'product/asset_account_list.html'
    context_object_name = 'asset_accounts'

class AssetAccountCreateView(SuccessMessageMixin, CreateView):
    model = AssetAccount
    fields = ['name', 'description', 'account_code', 'depreciation_account', 
              'allowance_account', 'depreciation_period']
    template_name = 'product/asset_account_form.html'
    success_url = reverse_lazy('asset-account-list')
    success_message = _("Asset account successfully created.")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add Bootstrap classes to all fields
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form

class AssetAccountUpdateView(SuccessMessageMixin, UpdateView):
    model = AssetAccount
    fields = ['name', 'description', 'account_code', 'depreciation_account', 
              'allowance_account', 'depreciation_period']
    template_name = 'product/asset_account_form.html'
    success_url = reverse_lazy('asset-account-list')
    success_message = _("Asset account successfully updated.")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add Bootstrap classes to all fields
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form

class AssetAccountDeleteView(DeleteView):
    model = AssetAccount
    template_name = 'product/asset_account_confirm_delete.html'
    success_url = reverse_lazy('asset-account-list')

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.product_set.exists():
            messages.error(request, _('Cannot delete asset account. It is used by one or more products.'))
            return redirect('asset-account-list')
        return super().get(request, *args, **kwargs)

