from django.shortcuts import render, redirect
from django.http import Http404
from django.utils.http import is_safe_url
from django.views.generic import ListView, UpdateView
from django.core.urlresolvers import reverse

from .forms import AddressForm
from .models import Address
from billing.models import BillingProfile


def checkout_address_create_view(request):
    form = AddressForm(request.POST or None)
    next_ = request.GET.get('next')
    next_post = request.POST.get('next')
    redirect_path = next_ or next_post or None

    if form.is_valid():
        print(request.POST)

        instance = form.save(commit=False)  # Model objects can be created directly from the ModelForm
        billing_profile, billing_profile_created = BillingProfile.objects.get_or_new(request)
        if billing_profile is not None:
            instance.billing_profile = billing_profile
            instance.address_type = request.POST.get('address_type', 'shipping')
            instance.save()
            request.session[instance.address_type + '_address_id'] = instance.id
            print(instance.address_type + '_address_id')
        else:
            print('Error in saving the address')
            return redirect('cart:checkout')

        if is_safe_url(redirect_path, request.get_host()):
            return redirect(redirect_path)

    return redirect('cart:checkout')


def checkout_address_reuse_view(request):
    if request.user.is_authenticated():
        next_ = request.GET.get('next')
        next_post = request.POST.get('next')
        redirect_path = next_ or next_post or None
        if request.method == 'POST':
            print(request.POST)
            address_id = request.POST.get('address_id', None)
            address_type = request.POST.get('address_type', 'shipping')
            billing_profile, billing_profile_created = BillingProfile.objects.get_or_new(request)
            if address_id is not None:
                qs = Address.objects.filter(billing_profile=billing_profile, id=address_id)
                if qs.exists():
                    request.session[address_type + '_address_id'] = address_id
                if is_safe_url(redirect_path, request.get_host()):
                    return redirect(redirect_path)
                    
    return redirect('cart:checkout')


class AddressListView(ListView):
    template_name = 'addresses/list.html'

    def get_queryset(self):
        return Address.objects.by_request(self.request)

    def get_context_data(self, *args, **kwargs):
        context = super(AddressListView, self).get_context_data(*args, **kwargs)
        context['edit_address'] = True
        return context


class AddressUpdateView(UpdateView):
    form_class = AddressForm
    template_name = 'addresses/detail_update.html'

    def get_object(self):
        qs = Address.objects.by_request(self.request).filter(pk=self.kwargs.get('address_id'))
        if qs.count() == 1:
            return qs.first()
        raise Http404

    def get_context_data(self, *args, **kwargs):
        context = super(AddressUpdateView, self).get_context_data(*args, **kwargs)
        context['title'] = 'Edit Address'
        return context

    def get_success_url(self):
        '''
        This is used instead of using the class variable 'success_url' because class variable
        cannot be used with reverse
        '''
        return reverse('address:list')
