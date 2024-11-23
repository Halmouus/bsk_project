from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Checker, Check, Invoice, Supplier
from .forms import InvoiceForm  # Import the custom form here
from django.forms import inlineformset_factory
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
import json
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from dateutil.parser import parse


class CheckerListView(ListView):
    model = Checker
    template_name = 'checker/checker_list.html'
    context_object_name = 'checkers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bank_choices'] = Checker.BANK_CHOICES
        return context

@method_decorator(csrf_exempt, name='dispatch')
class CheckerCreateView(View):
        def post(self, request):
            try:
                print("Received data:", request.body)
                data = json.loads(request.body)
                print("Parsed data:", data)
                
                # Validate final page
                starting_page = int(data['starting_page'])
                num_pages = int(data['num_pages'])
                calculated_final = starting_page + num_pages - 1
                
                checker = Checker.objects.create(
                    type=data['type'],
                    bank=data['bank'],
                    account_number=data['account_number'],
                    city=data['city'],
                    num_pages=num_pages,
                    index=data['index'].upper(),
                    starting_page=starting_page,
                    final_page=calculated_final
                )
                
                return JsonResponse({
                    'message': 'Checker created successfully',
                    'checker_id': str(checker.id)
                })
                
            except Exception as e:
                print("Error:", e)
                return JsonResponse({'error': str(e)}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class CheckerDetailsView(View):
        def get(self, request, pk):
            try:
                checker = get_object_or_404(Checker, pk=pk)
                return JsonResponse({
                    'code': checker.code,
                    'type': checker.type,
                    'bank': checker.get_bank_display(),
                    'account_number': checker.account_number,
                    'city': checker.city,
                    'num_pages': checker.num_pages,
                    'index': checker.index,
                    'starting_page': checker.starting_page,
                    'final_page': checker.final_page,
                    'current_position': checker.current_position,
                    'remaining_pages': checker.final_page - checker.current_position + 1
                })
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)

class CheckerDeleteView(View):
    def post(self, request, pk):
        try:
            checker = get_object_or_404(Checker, pk=pk)
            if checker.checks.exists():
                return JsonResponse({'error': 'Cannot delete checker with existing checks'}, status=400)
            checker.delete()
            return JsonResponse({'message': 'Checker deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


def invoice_autocomplete(request):
    query = request.GET.get('term', '')
    supplier_id = request.GET.get('supplier')
    print("Query:", query)  # Debug
    print("Supplier ID:", supplier_id)  # Debug
    
    invoices = Invoice.objects.filter(
        supplier_id=supplier_id,
        ref__icontains=query
    )
    print("Found invoices:", invoices.count())  # Debug
    print("Query SQL:", invoices.query)  # Debug
    
    invoice_list = [{
        'label': f"{i.ref} ({i.date}) - {i.total_amount:,.2f}",
        'value': str(i.id),
        'amount': float(i.total_amount)
    } for i in invoices]
    
    print("Response:", invoice_list)  # Debug
    return JsonResponse(invoice_list, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class CheckCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            checker = get_object_or_404(Checker, pk=data['checker_id'])
            invoice = get_object_or_404(Invoice, pk=data['invoice_id'])

            payment_due = data.get('payment_due')
            if payment_due == "" or payment_due is None:
                payment_due = None
            
            check = Check.objects.create(
                checker=checker,
                creation_date=data.get('creation_date', timezone.now().date()),
                beneficiary=invoice.supplier,
                cause=invoice,
                payment_due=payment_due,
                amount_due=invoice.total_amount,
                amount=data['amount'],
                observation=data.get('observation', '')
            )
            
            return JsonResponse({
                'message': 'Check created successfully',
                'check_id': str(check.id)
            })
            
        except Exception as e:
            print("Error creating check:", str(e))  # Debug print
            return JsonResponse({'error': str(e)}, status=400)
    
class CheckListView(ListView):
    model = Check
    template_name = 'checker/check_list.html'
    context_object_name = 'checks'

    def get_queryset(self):
        return Check.objects.select_related('checker', 'beneficiary', 'cause')


@method_decorator(csrf_exempt, name='dispatch')
class CheckStatusView(View):
    def post(self, request, pk, action):
        try:
            check = get_object_or_404(Check, pk=pk)
            
            if action == 'delivered':
                if check.delivered:
                    return JsonResponse({'error': 'Check already delivered'}, status=400)
                check.delivered = True
            elif action == 'paid':
                if not check.delivered:
                    return JsonResponse({'error': 'Check must be delivered first'}, status=400)
                if check.paid:
                    return JsonResponse({'error': 'Check already paid'}, status=400)
                check.paid = True
            
            check.save()
            return JsonResponse({'message': f'Check marked as {action}'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


def supplier_autocomplete(request):
    query = request.GET.get('term', '')
    suppliers = Supplier.objects.filter(
        Q(name__icontains=query) | 
        Q(accounting_code__icontains=query)
    )[:10]
    
    supplier_list = [{
        "label": f"{supplier.name} ({supplier.accounting_code})",
        "value": str(supplier.id)
    } for supplier in suppliers]
    
    return JsonResponse(supplier_list, safe=False)

@method_decorator(csrf_exempt, name='dispatch')
class CheckUpdateView(View):
    def get(self, request, pk):
        try:
            check = get_object_or_404(Check, pk=pk)
            return JsonResponse({
                'id': str(check.id),
                'status': check.status,
                'delivered_at': check.delivered_at.strftime('%Y-%m-%dT%H:%M') if check.delivered_at else None,
                'paid_at': check.paid_at.strftime('%Y-%m-%dT%H:%M') if check.paid_at else None,
                'cancelled_at': check.cancelled_at.strftime('%Y-%m-%dT%H:%M') if check.cancelled_at else None,
                'cancellation_reason': check.cancellation_reason
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            check = get_object_or_404(Check, pk=pk)
            
            if 'delivered_at' in data:
                check.delivered_at = parse(data['delivered_at']) if data['delivered_at'] else None
                check.delivered = bool(check.delivered_at)
                if check.delivered_at:
                    check.status = 'delivered'
            
            if 'paid_at' in data:
                if data['paid_at'] and not check.delivered_at:
                    return JsonResponse({'error': 'Check must be delivered before being marked as paid'}, status=400)
                check.paid_at = parse(data['paid_at']) if data['paid_at'] else None
                check.paid = bool(check.paid_at)
                if check.paid_at:
                    check.status = 'paid'
            
            check.save()
            return JsonResponse({'message': 'Check updated successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        

@method_decorator(csrf_exempt, name='dispatch')
class CheckCancelView(View):
    def post(self, request, pk):
        try:
            data = json.loads(request.body)
            check = get_object_or_404(Check, pk=pk)
            
            if check.paid_at:
                return JsonResponse({'error': 'Cannot cancel a paid check'}, status=400)
                
            check.cancelled_at = timezone.now()
            check.cancellation_reason = data.get('reason')
            check.status = 'cancelled'
            check.save()
            
            return JsonResponse({'message': 'Check cancelled successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)