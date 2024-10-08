from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import CategorySerializer, MenuItemSerializer, CartSerializer, OrderSerializer
from rest_framework.response import Response

from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404

from django.contrib.auth.models import Group, User

from rest_framework import viewsets
from rest_framework import status
# Create your views here.

class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    
    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    search_fields = ['category__title']
    ordering_fields = ['price', 'inventory']

    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]
    
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

class CartView(generics.ListCreateAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.all().filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        Cart.objects.all().filter(user = self.request.user).delete()
        return Response("ok")
    
class OrderView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Order.objects.all()
        elif self.request.user.groups.count()==0:
            return Order.objects.all().filter(user=self.request.user)
        elif self.request.user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.all().filter(delivery_crew=self.request.user)
        else:
            return Order.objects.all()
        #else :
        #   return Order.onjects.all()

def create(self, request, *args, **kwargs):
    menuitem_count = Cart.objects.all().filter(user=self.request.user).count()
    if menuitem_count == 0:
        return Response({"message:" : "no item in cart"})
    
    data = request.data.copy()
    total = self.get_total_price(self.request.user)
    data['total'] = total
    data['user'] = self.request.user.id
    order_serializer = OrderSerilaizer(data=data)
    if (order_serializer.is_valid()):
        order = order_serializer.save()

        items = Cart.objects.all().filter(user = self.reqest.user).all()

        for item in items.values():
            orderitem = OrderItem(
                order = order,
                menuitem_id = item['menuitem_id'],
                price = item['price'],
                quantity=item['quantity'],
            )
            orderitem.save()

        Cart.objects.all().filter(user=self.request.user).delete()

        result = order_serializer.data.copy()
        result['total'] = total
        return Response(order_serializer.data)
    
def get_total_price(self, user):
    total = 0
    items = Cart.objects.all().filter(user=user).all()
    for item in items.values():
        total += item['price']
    return total

class SingleOrderView(generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if self.request.user.groups.count()==0: 
            return Response('Not Ok')
        else : 
            return super().update(request, *args, **kwargs)
        
class GroupViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]
    def list(self, request):
        users = User.objects.all().filter(groups__name='Manager')
        items = UserSeriliazer(users, many=True)
        return Response(items.data)
    
    def create(self, request):
        user = get_object_or_404(User, username=request.data['username'])
        managers = Group.objects.get(name = "Manager")
        managers.user_set.add(user)
        return Response({"message" : "user added to the manager group"}, 200)
    
    def destroy(self, request):
        user = get_objects_or_404(User, username= request.data['username'])
        managers = Group.objects.get(name="Manager")
        managers.user_set.remove(user)
        return Response({"message" : "user removed from the manager group"}, 200)
    
class DeliveryCrewViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        users = User.objects.all().filter(groups__name='Delivery Crew')
        items = UserSerializer(users, many=True)
        return Response(items.data)
    
    def create(self, request):
        if self.request.user.is_superuser == False:
            if self.request.user.groups.filter(name= 'Manager').exists() == False:
                return Response({"message" : "forbidden"}, status.HTTP_FORBIDDEN)
            
            user = get_object_or_404(User, username=request.data['username'])
            dc = Group.objects.get(name="Delivey Crew")
            dc.user_set.add(user)
            return Response({"message" : "user added to the delivery creq group"}, 200)
        
    def destroy(self,request):
        if self.requset.user.is_superuser == False:
            if self.request.user.groups.filter(name = 'Manager').exists() == False:
                return Response({"message": "forbidden"}, status.HTTP_403_FORBIDDEN)
            user = get_object_or_404(User, username=request.data['username'])
            dc = Group.objects.get(name="Delivery Crew")
            dc.user_set.remove(user)
            return Response({"message": "user removed from the delivery creq group"}, 200)