from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _

from .models import DeliveryNote, ReceptionNote, Invoice
from .forms import DeliveryNoteForm, ReceptionNoteForm

class DeliveryNoteListView(ListView):
    model = DeliveryNote
    template_name = 'notes/delivery_note_list.html'
    context_object_name = 'notes'

    def get_queryset(self):
        queryset = super().get_queryset()
        print("Fetching delivery notes")
        
        # Filter options
        ref = self.request.GET.get('ref')
        supplier_id = self.request.GET.get('supplier_id')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        linked = self.request.GET.get('linked')

        if ref:
            print(f"Filtering by ref: {ref}")
            queryset = queryset.filter(ref__icontains=ref)
        
        if date_from:
            print(f"Filtering from date: {date_from}")
            queryset = queryset.filter(date__gte=date_from)
            
        if date_to:
            print(f"Filtering to date: {date_to}")
            queryset = queryset.filter(date__lte=date_to)

        if supplier_id:
            print(f"Filtering by supplier: {supplier_id}")
            queryset = queryset.filter(supplier_id=supplier_id)

        if linked:
            print(f"Filtering by linked status: {linked}")
            if linked == 'yes':
                queryset = queryset.filter(invoices__isnull=False)
            elif linked == 'no':
                queryset = queryset.filter(invoices__isnull=True)

        return queryset.order_by('-date')

class DeliveryNoteCreateView(CreateView):
    model = DeliveryNote
    form_class = DeliveryNoteForm
    template_name = 'notes/delivery_note_list.html'
    success_url = reverse_lazy('delivery-note-list')

    def form_valid(self, form):
        try:
            self.object = form.save()
            return JsonResponse({
                'success': True,
                'message': _('Delivery note created successfully.')
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    def form_invalid(self, form):
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })

class DeliveryNoteUpdateView(UpdateView):
    model = DeliveryNote
    template_name = 'notes/delivery_note_list.html'
    fields = ['ref', 'date', 'supplier', 'amount', 'document', 'notes']
    
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            note = self.get_object()
            data = {
                'id': str(note.id),
                'ref': note.ref,
                'date': note.date.strftime('%Y-%m-%d'),
                'supplier_id': str(note.supplier.id) if note.supplier else None,
                'supplier_name': note.supplier.name if note.supplier else None,
                'amount': float(note.amount) if note.amount else None,
                'notes': note.notes,
                'document_url': note.document.url if note.document else None
            }
            return JsonResponse(data)
            
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        note = self.get_object()
        try:
            # Update fields from form data
            note.ref = request.POST.get('ref')
            note.date = request.POST.get('date')
            note.supplier_id = request.POST.get('supplier')
            note.amount = request.POST.get('amount') or None
            note.notes = request.POST.get('notes')
            
            # Handle document upload if provided
            if 'document' in request.FILES:
                note.document = request.FILES['document']
            
            note.save()
            return JsonResponse({'success': True, 'message': _('Delivery note updated successfully.')})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
@method_decorator(csrf_exempt, name='dispatch')
class DeliveryNoteDeleteView(DeleteView):
    model = DeliveryNote
    success_url = reverse_lazy('delivery-note-list')

    def post(self, request, *args, **kwargs):
        print("\n=== Processing Delete Request ===")
        print(f"Note ID: {kwargs.get('pk')}")
        
        self.object = self.get_object()
        print(f"Found note: {self.object.ref}")
        
        self.object.delete()
        print("Note deleted successfully")
        
        return JsonResponse({'success': True, 'message': _('Delivery note deleted successfully.')})

class AvailableDeliveryNotesView(View):
    def get(self, request):
        print("Fetching available delivery notes")
        # Get notes that aren't linked to any invoice
        notes = DeliveryNote.objects.filter(invoices__isnull=True)
        
        # Search functionality
        search = request.GET.get('term', '')
        if search:
            notes = notes.filter(ref__icontains=search)

        data = [{
            'id': str(note.id),
            'text': f"BL {note.ref} ({note.date})",
            'ref': note.ref,
            'date': note.date.strftime('%Y-%m-%d'),
            'amount': float(note.amount) if note.amount else None
        } for note in notes]

        return JsonResponse(data, safe=False)

class ReceptionNoteListView(ListView):
    model = ReceptionNote
    template_name = 'notes/reception_note_list.html'
    context_object_name = 'notes'

    def get_queryset(self):
        queryset = super().get_queryset()
        print("Fetching reception notes")
        
        # Filter options
        ref = self.request.GET.get('ref')
        supplier_id = self.request.GET.get('supplier_id')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        linked = self.request.GET.get('linked')

        if ref:
            print(f"Filtering by ref: {ref}")
            queryset = queryset.filter(ref__icontains=ref)
        
        if date_from:
            print(f"Filtering from date: {date_from}")
            queryset = queryset.filter(date__gte=date_from)
            
        if date_to:
            print(f"Filtering to date: {date_to}")
            queryset = queryset.filter(date__lte=date_to)

        if supplier_id:
            print(f"Filtering by supplier: {supplier_id}")
            queryset = queryset.filter(supplier_id=supplier_id)

        if linked:
            print(f"Filtering by linked status: {linked}")
            if linked == 'yes':
                queryset = queryset.filter(invoices__isnull=False)
            elif linked == 'no':
                queryset = queryset.filter(invoices__isnull=True)

        return queryset.order_by('-date')

class ReceptionNoteCreateView(CreateView):
    model = ReceptionNote
    form_class = ReceptionNoteForm
    template_name = 'notes/reception_note_list.html'
    success_url = reverse_lazy('reception-note-list')

    def form_valid(self, form):
        try:
            self.object = form.save()
            return JsonResponse({
                'success': True,
                'message': _('Reception note created successfully.')
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        
    def form_invalid(self, form):
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })

class ReceptionNoteUpdateView(UpdateView):
    model = ReceptionNote
    template_name = 'notes/reception_note_list.html'
    fields = ['ref', 'date', 'supplier', 'amount', 'document', 'notes']

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            note = self.get_object()
            data = {
                'id': str(note.id),
                'ref': note.ref,
                'date': note.date.strftime('%Y-%m-%d'),
                'supplier_id': str(note.supplier.id) if note.supplier else None,
                'supplier_name': note.supplier.name if note.supplier else None,
                'amount': float(note.amount) if note.amount else None,
                'notes': note.notes,
                'document_url': note.document.url if note.document else None
            }
            return JsonResponse(data)
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        note = self.get_object()
        try:
            note.ref = request.POST.get('ref')
            note.date = request.POST.get('date')
            note.supplier_id = request.POST.get('supplier')
            note.amount = request.POST.get('amount') or None
            note.notes = request.POST.get('notes')
            
            if 'document' in request.FILES:
                note.document = request.FILES['document']
            
            note.save()
            return JsonResponse({'success': True, 'message': _('Reception note updated successfully.')})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
@method_decorator(csrf_exempt, name='dispatch')
class ReceptionNoteDeleteView(DeleteView):
    model = ReceptionNote
    success_url = reverse_lazy('reception-note-list')

    def post(self, request, *args, **kwargs):
        print("\n=== Processing Delete Request ===")
        print(f"Note ID: {kwargs.get('pk')}")
        
        self.object = self.get_object()
        print(f"Found note: {self.object.ref}")
        
        self.object.delete()
        print("Note deleted successfully")
        
        return JsonResponse({'success': True, 'message': _('Reception note deleted successfully.')})

class AvailableReceptionNotesView(View):
    def get(self, request):
        print("Fetching available reception notes")
        # Get notes that aren't linked to any invoice
        notes = ReceptionNote.objects.filter(invoices__isnull=True)
        
        # Search functionality
        search = request.GET.get('term', '')
        if search:
            notes = notes.filter(ref__icontains=search)

        data = [{
            'id': str(note.id),
            'text': f"BR {note.ref} ({note.date})",
            'ref': note.ref,
            'date': note.date.strftime('%Y-%m-%d'),
            'amount': float(note.amount) if note.amount else None
        } for note in notes]

        return JsonResponse(data, safe=False)
