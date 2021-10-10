from django.shortcuts import get_object_or_404, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.db import transaction

from django.forms import inlineformset_factory

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView

from geekshop.basketapp.models import Basket
from geekshop.ordersapp.models import Order, OrderItem
from geekshop.ordersapp.forms import OrderItemForm
from django.dispatch import receiver
from django.db.models.signals import pre_save, pre_delete
from django.http import JsonResponse
from geekshop.mainapp.models import Product


class OrderItemsCreate(CreateView):
    model = Order
    fields = []
    success_url = reverse_lazy('ordersapp:orders_list')

    def __init__(self, form=None, **kwargs):
        super().__init__(kwargs)
        self.object = form.save()

    def get_context_data(self, **kwargs):
        global num
        data = super(OrderItemsCreate, self).get_context_data(**kwargs)
        OrderFormSet = inlineformset_factory(Order, OrderItem, \
                                            form=OrderItemForm, extra=1)

        if self.request.POST:
           formset = OrderFormSet(self.request.POST)
        else:
            basket_items = Basket.get_items(self.request.user)
            if len(basket_items):
                OrderFormSet = inlineformset_factory(Order, OrderItem, \
                                    form=OrderItemForm, extra=len(basket_items))
                formset = OrderFormSet()
                for num, form in enumerate(formset.forms):
                    form.initial['product'] = basket_items[num].product
                    form.initial['quantity'] = basket_items[num].quantity
                    form.initial['price'] = basket_items[num].product.price
                basket_items[num].delete()
            else:
                formset = OrderFormSet()

        data['orderitems'] = formset
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        orderitems = context['orderitems']

        with transaction.atomic():
            form.instance.user = self.request.user
            if orderitems.is_valid():
                orderitems.instance = self.object
                orderitems.save()

        # удаляем пустой заказ
        if self.object.get_total_cost() == 0:
            self.object.delete()

        return super(OrderItemsCreate, self).form_valid(form)


    def order_forming_complete(pk):
        order = get_object_or_404(Order, pk=pk)
        order.status = Order.SENT_TO_PROCEED
        order.save()

        return HttpResponseRedirect(reverse('ordersapp:orders_list'))


class OrderFormSet(object):
    pass


class OrderItemsUpdate(UpdateView):

    def get_context_data(self, data=None, **kwargs):

        if self.request.POST:
            data['orderitems'] = OrderFormSet(self.request.POST)
        else:
            formset = OrderFormSet(instance=self.object)
            for form in formset.forms:
                if form.instance.pk:
                    form.initial['price'] = form.instance.product.price
            data['orderitems'] = formset
        return data


class OrderRead(DetailView):
    model = Order

    def get_context_data(self, **kwargs):
        context = super(OrderRead, self).get_context_data(**kwargs)
        context['title'] = 'заказ/просмотр'
        return context


class OrderDelete(DeleteView):
    model = Order
    success_url = reverse_lazy('ordersapp:orders_list')


class OrderList(ListView):
    model = Order

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

@receiver(pre_save, sender=OrderItem)
@receiver(pre_save, sender=Basket)
def product_quantity_update_save(sender, update_fields, instance, **kwargs):
    if update_fields is 'quantity' or 'product':
        if instance.pk:
            instance.product.quantity -= instance.quantity - \
                                        sender.get_item(instance.pk).quantity
        else:
            instance.product.quantity -= instance.quantity
        instance.product.save()


@receiver(pre_delete, sender=OrderItem)
@receiver(pre_delete, sender=Basket)
def product_quantity_update_delete(sender, instance, **kwargs):
    instance.product.quantity += instance.quantity
    instance.product.save()

def get_product_price(request, pk):
   if request.is_ajax():
       product = Product.objects.filter(pk=int(pk)).first()
       if product:
           return JsonResponse({'price': product.price})
       else:
           return JsonResponse({'price': 0})


def order_forming_complete():
    return None