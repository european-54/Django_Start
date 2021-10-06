from django.db import models
from django.conf import settings
from mainapp.models import Product


class BasketQuerySet(models.QuerySet):

   def delete(self, *args, **kwargs):
       for object in self:
           object.product.quantity += object.quantity
           object.product.save()
       super(BasketQuerySet, self).delete(*args, **kwargs)

objects = BasketQuerySet.as_manager()


class Basket(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
on_delete=models.CASCADE, related_name='basket')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='количество',
default=0)
    add_datetime = models.DateTimeField(verbose_name='время',
auto_now_add=True)


def property(args):
    pass


@property
def product_cost(self):
    "return cost of all products this type"
    return self.product.price * self.quantity


def sum(param):
    pass


def list(param):
    pass


def map(param, _items):
    pass


def property(args):
    pass


@property
def total_quantity(self):
    "return total quantity for user"
    _items = Basket.objects.filter(user=self.user)
    _totalquantity = sum(list(map(lambda x: x.quantity, _items)))
    return _totalquantity

@property
def total_cost(self, total=None):
    "return total cost for user"
    _items = Basket.objects.filter(user=self.user)
    _totalcost = sum(list(map(lambda x: x.product_cost, _items)))
    return _totalcost
