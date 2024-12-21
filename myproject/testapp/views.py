from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache, cache_control
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from .views_supplier import SupplierListView, SupplierCreateView, SupplierUpdateView, SupplierDeleteView
from django.views.decorators.http import require_http_methods
from .models import Entity, Client, CheckReceipt, LCN
import json


# Create your views here.
def home(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')  # Redirect to the profile view after successful login
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'login.html')  # Render the login template

@never_cache
@login_required
@cache_control(no_store=True, no_cache=True, must_revalidate=True)
def profile(request):
    return render(request, 'profile.html')  # Use 'profile.html' directly


class CustomLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        messages.success(self.request, f'Welcome, {form.get_user().first_name}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)

# Custom logout view to prevent back button access after logout
@cache_control(no_cache=True, must_revalidate=True)
def logout_view(request):
    logout(request)
    # Redirect to the login page after logout
    response = HttpResponseRedirect('/')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@require_http_methods(["POST"])
def check_receipt_duplicate(request):
    data = json.loads(request.body)
    number = data.get('number')
    entity = data.get('entity')
    bank = data.get('bank')
    receipt_type = data.get('receipt_type')
    
    if receipt_type == 'check':
        exists = CheckReceipt.objects.filter(
            check_number=number,
            entity_id=entity,
            issuing_bank=bank
        ).exists()
    else:
        exists = LCN.objects.filter(
            lcn_number=number,
            entity_id=entity,
            issuing_bank=bank
        ).exists()
    
    return JsonResponse({'exists': exists})

@require_http_methods(["GET"])
def validate_entity(request, entity_id):
    valid = Entity.objects.filter(id=entity_id).exists()
    return JsonResponse({'valid': valid})

@require_http_methods(["GET"])
def validate_client(request, client_id):
    valid = Client.objects.filter(id=client_id).exists()
    return JsonResponse({'valid': valid})

@require_http_methods(["GET"])
def validate_receipt(request, receipt_id):
    # Check both CheckReceipt and LCN models
    valid = (
        CheckReceipt.objects.filter(id=receipt_id).exists() or
        LCN.objects.filter(id=receipt_id).exists()
    )
    return JsonResponse({'valid': valid})