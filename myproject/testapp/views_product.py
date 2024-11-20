from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Product
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# List all Products
class ProductListView(ListView):
    model = Product
    template_name = 'product/product_list.html'
    context_object_name = 'products'

# Create a new Product
class ProductCreateView(SuccessMessageMixin, CreateView):
    model = Product
    fields = ['name', 'vat_rate', 'expense_code', 'is_energy', 'fiscal_label']
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully created."

# Update an existing Product
class ProductUpdateView(SuccessMessageMixin, UpdateView):
    model = Product
    fields = ['name', 'vat_rate', 'expense_code', 'is_energy', 'fiscal_label']
    template_name = 'product/product_form.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully updated."

# Delete a Product
class ProductDeleteView(DeleteView):
    model = Product
    template_name = 'product/product_confirm_delete.html'
    success_url = reverse_lazy('product-list')
    success_message = "Product successfully deleted."

# AJAX view for creating a new Product
@method_decorator(csrf_exempt, name='dispatch')
class ProductAjaxCreateView(View):
    def post(self, request):
        try:
            product = Product.objects.create(
                name=request.POST.get('name'),
                fiscal_label=request.POST.get('fiscal_label'),
                is_energy=request.POST.get('is_energy') == 'true',
                expense_code=request.POST.get('expense_code'),
                vat_rate=request.POST.get('vat_rate')
            )
            return JsonResponse({
                'message': 'Product created successfully',
                'product_id': str(product.id)  # Convert UUID to string
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
                'vat_rate': float(product.vat_rate)
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)