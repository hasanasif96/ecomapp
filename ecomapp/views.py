from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View, CreateView,FormView, DetailView, ListView
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from .utils import password_reset_token
from django.db.models import Q
from django.conf import settings
from django.core.mail import send_mail
from .models import *
from django.urls import reverse_lazy, reverse
from .forms import *
from django.contrib import messages
# Create your views here.


class EcomMixin(object):
    def dispatch(self, request, *args, **kwargs):
        cart_id = request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            if request.user.is_authenticated and request.user.customer:
                cart_obj.customer = request.user.customer
                cart_obj.save()
        return super().dispatch(request, *args, **kwargs)

class cartnum(object):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = None
        context['cart'] = cart
        return context
   

class HomeView(EcomMixin, cartnum, TemplateView):
    template_name= "home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_products'] = Product.objects.all()
        return context
    
class contact(cartnum, EcomMixin, TemplateView):
    template_name= "contact.html"
    
class AllProductsView(cartnum,EcomMixin, TemplateView):
    template_name = "allproducts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['allcategories'] = Category.objects.all()
        return context

class ProductDetailView(cartnum,EcomMixin, TemplateView):
    template_name = "productdetail.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_slug = self.kwargs['slug']
        product = Product.objects.get(slug=url_slug)
        similar_product = Product.objects.filter(category=product.category).exclude(slug=url_slug)
        product.view_count += 1
        product.save()
        context['product'] = product
        context['sim_prod'] = similar_product
        return context

    
    
    

class AddToCartView(cartnum,EcomMixin, View):

    #def get_context_data(self,request, *args, **kwargs):
    #    context = super().get_context_data(**kwargs)
    def get(self, request, *args, **kwargs):
        print(request.get_full_path)
        # get product id from requested url
        product_id = self.kwargs['pro_id']
        # get product
        product_obj = Product.objects.get(id=product_id)

        # check if cart exists
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            this_product_in_cart = cart_obj.cartproduct_set.filter(
                product=product_obj)

            # item already exists in cart
            if this_product_in_cart.exists():
                cartproduct = this_product_in_cart.last()
                cartproduct.quantity += 1
                cartproduct.subtotal += product_obj.selling_price
                cartproduct.save()
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
            # new item is added in cart
            else:
                cartproduct = CartProduct.objects.create(
                    cart=cart_obj, product=product_obj, rate=product_obj.selling_price, quantity=1, subtotal=product_obj.selling_price)
                cart_obj.total += product_obj.selling_price
                cart_obj.save()
                


        else:
            cart_obj = Cart.objects.create(total=0)
            self.request.session['cart_id'] = cart_obj.id
            cartproduct = CartProduct.objects.create(
                cart=cart_obj, product=product_obj, rate=product_obj.selling_price, quantity=1, subtotal=product_obj.selling_price)
            cart_obj.total += product_obj.selling_price
            cart_obj.save()
        messages.success(request, 'Product added to the cart')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))



class MyCartView(cartnum,EcomMixin, TemplateView):
    template_name = "mycart.html"
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart = Cart.objects.get(id=cart_id)
        else:
            cart = None
        context['cart'] = cart
        return context
    
    
class ManageCartView(EcomMixin, View):
    def get(self, request, *args, **kwargs):
        cp_id = self.kwargs["cp_id"]
        action = request.GET.get("action")
        cp_obj = CartProduct.objects.get(id=cp_id)
        cart_obj = cp_obj.cart

        if action == "inc":
            cp_obj.quantity += 1
            cp_obj.subtotal += cp_obj.rate
            cp_obj.save()
            cart_obj.total += cp_obj.rate
            cart_obj.save()
        elif action == "dcr":
            cp_obj.quantity -= 1
            cp_obj.subtotal -= cp_obj.rate
            cp_obj.save()
            cart_obj.total -= cp_obj.rate
            cart_obj.save()
            if cp_obj.quantity == 0:
                cp_obj.delete()

        elif action == "rmv":
            cart_obj.total -= cp_obj.subtotal
            cart_obj.save()
            cp_obj.delete()
        else:
            pass
        return redirect("ecomapp:mycart")



class CheckoutView(EcomMixin, CreateView):
    template_name = "checkout.html"
    form_class = CheckoutForm
    success_url = reverse_lazy("ecomapp:orderplaced")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.customer:
            pass
        else:
            return redirect("/login/?next=/checkout/")
        return super().dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_id = self.request.session.get("cart_id", None)
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
        else:
            cart_obj = None
        context['cart'] = cart_obj
        return context
    
    
    def form_valid(self, form):
        cart_id = self.request.session.get("cart_id")
        if cart_id:
            cart_obj = Cart.objects.get(id=cart_id)
            form.instance.cart = cart_obj
            form.instance.subtotal = cart_obj.total
            form.instance.discount = 0
            form.instance.total = cart_obj.total
            #print(form['email'].value())
            form.instance.order_status = "Order Received"
            subject = 'Order Placed'
            message = f'Hi, thank you for placing an order.'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [form['email'].value(), ]
            send_mail( subject, message, email_from, recipient_list )
            del self.request.session['cart_id']
        else:
            return redirect("ecomapp:home")
        return super().form_valid(form)

  

class OrderplacedView(cartnum,TemplateView):
    template_name = "orderdone.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.customer
        context['customer'] = customer
        orders = Order.objects.filter(cart__customer=customer).order_by("-id")[0]
        #order_id=orders.id
        cart_pro = CartProduct.objects.get(id=orders.cart.id)
        cat=Cart.objects.get(id=orders.cart.id)
        context["cart_pros"] = cat
        context["orders"] = orders
        return context
    
    
class CustomerRegistrationView(CreateView):
    template_name = "customerregistration.html"
    form_class = CustomerRegistrationForm
    success_url = reverse_lazy("ecomapp:home")
    
    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        email = form.cleaned_data.get("email")
        user = User.objects.create_user(username, email, password)
        form.instance.user = user
        login(self.request, user)
        subject = 'welcome to CityMart'
        message = f'Hi {user.username}, thank you for registering in FtpMart.'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [user.email, ]
        send_mail( subject, message, email_from, recipient_list )
        return super().form_valid(form)


class CustomerLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("ecomapp:home")


class CustomerLoginView(FormView):
    template_name = "customerlogin.html"
    form_class = CustomerLoginForm
    success_url = reverse_lazy("ecomapp:home")

    def form_valid(self, form):
        uname = form.cleaned_data.get("username")
        pword = form.cleaned_data["password"]
        usr = authenticate(username=uname, password=pword)
        if usr is not None and usr.customer:
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {"form": self.form_class, "error": "Invalid credentials"})

        return super().form_valid(form)

    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url

class CustomerProfileView(cartnum,TemplateView):
    template_name = "customerprofile.html"
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.customer:
            pass
        else:
            return redirect("/login/?next=/profile/")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.request.user.customer
        context['customer'] = customer
        orders = Order.objects.filter(cart__customer=customer).order_by("-id")
        context["orders"] = orders
        return context

    
ORDER_STATUS2 = (
    ("Order Cancelled", "Cancel Order"),
    ("Return Requested","Request Return"),
    
)   
class CustomerOrderDetailView(cartnum, DetailView):
    template_name = "customerorderdetail.html"
    model = Order
    context_object_name = "ord_obj"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Customer.objects.filter(user=request.user).exists():
            order_id = self.kwargs["pk"]
            order = Order.objects.get(id=order_id)
            if request.user.customer != order.cart.customer:
                return redirect("ecomapp:customerprofile")
        else:
            return redirect("/login/?next=/profile/")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["allstatus"] = ORDER_STATUS2
        return context
    
    def post(self, request, *args, **kwargs):
        order_id = self.kwargs["pk"]
        order_obj = Order.objects.get(id=order_id)
        new_status = request.POST.get("status")
        order_obj.order_status = new_status
        order_obj.save()
        return redirect(reverse_lazy("ecomapp:customerorderdetail", kwargs={"pk": order_id}))


class SearchView(TemplateView):
    template_name = "search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kw = self.request.GET.get("keyword")
        results = Product.objects.filter(
            Q(title__icontains=kw) | Q(description__icontains=kw) | Q(return_policy__icontains=kw))
        print(results)
        context["results"] = results
        return context

class PasswordForgotView(FormView):
    template_name = "forgotpassword.html"
    form_class = PasswordForgotForm
    success_url = "/forgot-password/?m=s"
    
    def form_valid(self, form):
        # get email from user
        email = form.cleaned_data.get("email")
        # get current host ip/domain
        url = self.request.META['HTTP_HOST']
        # get customer and then user
        customer = Customer.objects.filter(user__email=email)[0]
        print(customer)
        user = customer.user
        text_content = 'Please Click the link below to reset your password. '
        html_content = url + "/password-reset/" + email + \
                "/" + password_reset_token.make_token(user) + "/"
    
        send_mail(
                'Password Reset Link | Django Ecommerce',
                text_content + html_content,
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
        return super().form_valid(form)
#aadmin
        
class AdminLoginView(FormView):
    template_name = "admin/adminlogin.html"
    form_class = CustomerLoginForm
    success_url = reverse_lazy("ecomapp:adminhome")

    def form_valid(self, form):
        uname = form.cleaned_data.get("username")
        pword = form.cleaned_data["password"]
        usr = authenticate(username=uname, password=pword)
        if usr is not None and Admin.objects.filter(user=usr).exists():
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {"form": self.form_class, "error": "Invalid credentials"})
        return super().form_valid(form)


class AdminRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Admin.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect("/admin-login/")
        return super().dispatch(request, *args, **kwargs)


class AdminHomeView(AdminRequiredMixin, TemplateView):
    template_name = "admin/adminhome.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pendingorders"] = Order.objects.filter(
            order_status="Order Received").order_by("-id")
        return context


class AdminOrderDetailView(AdminRequiredMixin, DetailView):
    template_name = "admin/adminorderdetail.html"
    model = Order
    context_object_name = "ord_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["allstatus"] = ORDER_STATUS
        return context


class AdminOrderListView(AdminRequiredMixin, ListView):
    template_name = "admin/adminorderlist.html"
    queryset = Order.objects.all().order_by("-id")
    context_object_name = "allorders"


class AdminOrderStatuChangeView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order_id = self.kwargs["pk"]
        order_obj = Order.objects.get(id=order_id)
        new_status = request.POST.get("status")
        order_obj.order_status = new_status
        order_obj.save()
        subject = "Update on your order "
        message = f'Hi {order_obj.ordered_by}, status of your changed to {new_status}.'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [order_obj.email, ]
        send_mail( subject, message, email_from, recipient_list )
        return redirect(reverse_lazy("ecomapp:adminorderdetail", kwargs={"pk": order_id}))


class AdminProductListView(AdminRequiredMixin, ListView):
    template_name = "admin/adminproductlist.html"
    queryset = Product.objects.all().order_by("-id")
    context_object_name = "allproducts"


class AdminProductCreateView(AdminRequiredMixin, CreateView):
    template_name = "admin/adminproductcreate.html"
    form_class = ProductForm
    success_url = reverse_lazy("ecomapp:adminproductlist")

    def form_valid(self, form):
        p = form.save()
        images = self.request.FILES.getlist("more_images")
        for i in images:
            ProductImage.objects.create(product=p, image=i)
        return super().form_valid(form)

    
    
   #Delivery backend
    
    
class DeliveryRegistrationView(CreateView):
    template_name = "Deliveryregistration.html"
    form_class = DeliveryRegistrationForm
    success_url = reverse_lazy("ecomapp:DeliveryOrderList")
    
    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        password = form.cleaned_data.get("password")
        email = form.cleaned_data.get("email")
        user = User.objects.create_user(username,email, password)
        #Delivery.objects.create_user(user,full_name, mobile)
        form.instance.user = user
        login(self.request, user)
        return super().form_valid(form)

class DeliveryLoginView(FormView):
    template_name = "Deliverylogin.html"
    form_class = CustomerLoginForm
    success_url = reverse_lazy("ecomapp:DeliveryOrderList")

    def form_valid(self, form):
        uname = form.cleaned_data.get("username")
        pword = form.cleaned_data["password"]
        usr = authenticate(username=uname, password=pword)
        if usr is not None and Delivery.objects.filter(user=usr).exists():
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {"form": self.form_class, "error": "Invalid credentials"})
        return super().form_valid(form)
    

    
    
class DeliveryRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Delivery.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect("/Delivery-login/")
        return super().dispatch(request, *args, **kwargs)

class DeliveryOrderListView(DeliveryRequiredMixin, ListView):
    template_name = "deliveryallorder.html"
    queryset = Order.objects.filter(agent ="No one assigned").order_by("-id")
    context_object_name = "allorders"
    
    
class Currentdelivery(DeliveryRequiredMixin, TemplateView):
    template_name = "Currentdelivery.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        name=self.request.user
        context["pendingorders"] = Order.objects.filter(agent=name).exclude(order_status="Order Completed").order_by("-id")
        return context


class pendingDeliveryOrderDetailView(DeliveryRequiredMixin, DetailView):
    template_name = "pendingdeliveryorderdetail.html"
    model = Order
    context_object_name = "ord_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["allstatus"] = ORDER_STATUS
        return context
    
class pendingDeliveryOrderStatuChangeView(DeliveryRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order_id = self.kwargs["pk"]
        order_obj = Order.objects.get(id=order_id)
        new_status = request.POST.get("status")
        order_obj.order_status = new_status
        order_obj.save()
        return redirect(reverse_lazy("ecomapp:pendingDeliveryOrderDetail", kwargs={"pk": order_id}))
    
    
class DeliveryOrderDetailView(DeliveryRequiredMixin,DetailView):
    template_name = "deliveryorderdetail.html"
    model = Order
    context_object_name = "ord_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["allstatus"] = ORDER_STATUS
        return context
    
    
class Deliverymanageview(DeliveryRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        r_id = self.kwargs["dk"]
        action = request.GET.get("action")
        agents=self.request.user
        request_obj = Order.objects.get(id=r_id)

        if action == "acc":
            request_obj.agent = str(agents)
            request_obj.save()
        else:
            pass
        return redirect("ecomapp:DeliveryOrderList")
    

    
class previousDeliveryOrderView(DeliveryRequiredMixin, TemplateView):
    template_name = "previousDeliveryOrder.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        name=self.request.user
        context["completedorders"] = Order.objects.filter(agent=name,order_status="Order Completed" ).order_by("-id")
        return context
