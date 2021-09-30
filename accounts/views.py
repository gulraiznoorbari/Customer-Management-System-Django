from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import OrderForm, CreateUserForm, CustomerForm
from .filters import OrderFilter
from .decorators import allowed_users, unauthenticated_user, admin_only

# Create your views here.

@unauthenticated_user
def registerPage(request):
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get("username")
            messages.success(request, "Account was created for " + username)
            return redirect("login")
    context = {"form":form}
    return render(request, "accounts/register.html", context)

@unauthenticated_user
def loginPage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.info(request, "Username or Password is incorrect!")

    context = {}
    return render(request, "accounts/login.html", context)

def logoutUser(request):
    logout(request)
    return redirect("login")

@login_required(login_url='login')
@allowed_users(allowed_roles=["customer"])
def userPage(request):
    orders = request.user.customer.order_set.all()
    total_orders = orders.count()
    orders_delivered = orders.filter(status="Delivered").count()
    orders_pending = orders.filter(status="Pending").count()
    context = {
        "orders":orders, 
        "total_orders":total_orders, 
        "orders_delivered":orders_delivered,
        "orders_pending":orders_pending,
    }
    return render(request, "accounts/user.html", context)

@login_required(login_url='login')
@allowed_users(allowed_roles=["customer"])
def accountSettings(request):
    customer = request.user.customer
    form = CustomerForm(instance=customer)
    if request.method == "POST":
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
    context = {"form":form}
    return render(request, 'accounts/account_settings.html', context)

@login_required(login_url='login')
@admin_only
def home(request):
    orders = Order.objects.all()
    total_orders = orders.count()
    orders_delivered = orders.filter(status="Delivered").count()
    orders_pending = orders.filter(status="Pending").count()
    customers = Customer.objects.all()
    total_customers = customers.count()
    
    context = {
        "orders":orders, 
        "customers":customers, 
        "total_orders":total_orders, 
        "orders_delivered":orders_delivered,
        "orders_pending":orders_pending,
    }
    return render(request, "accounts/dashboard.html", context)

@login_required(login_url='login')
@allowed_users(allowed_roles=["admin"])
def products(request):
    products = Product.objects.all()
    return render(request, "accounts/products.html", {"products":products})

@login_required(login_url='login')
@allowed_users(allowed_roles=["admin"])
def customer(request, primary_key):
    customer = Customer.objects.get(id=primary_key)
    orders = customer.order_set.all()
    order_count = orders.count()
    filter = OrderFilter(request.GET, queryset=orders)
    orders = filter.qs

    context = {
        "customer":customer,
        "orders":orders,
        "order_count":order_count,
        "filter":filter,
    }
    return render(request, "accounts/customer.html", context)

@login_required(login_url='login')
@allowed_users(allowed_roles=["admin"])
def createOrder(request, primary_key):
    OrderFormSet = inlineformset_factory(Customer, Order, fields=("product", "status"), extra=5)
    customer = Customer.objects.get(id=primary_key)
    formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)
    if request.method == "POST":
        formset = OrderFormSet(request.POST, instance=customer)
        if formset.is_valid():
            formset.save()
            return redirect("/")

    context = {"formset": formset}
    return render(request, "accounts/order_form.html", context)

@login_required(login_url='login')
@allowed_users(allowed_roles=["admin"])
def updateOrder(request, primary_key):
    order = Order.objects.get(id=primary_key)
    form = OrderForm(instance=order)
    if request.method == "POST":
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('/customer/' + str(order.customer.id))

    context = {"form": form}
    return render(request, "accounts/order_form.html", context)

@login_required(login_url='login')
@allowed_users(allowed_roles=["admin"])
def deleteOrder(request, primary_key):
    order = Order.objects.get(id=primary_key)
    if request.method == "POST":
        order.delete()
        return redirect("/")
    context = {"item": order}
    return render(request, "accounts/delete.html", context)


