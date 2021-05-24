# -*- coding: utf-8 -*-

from django.urls import path
from .views import *

app_name= "ecomapp"
urlpatterns=[
        path("", HomeView.as_view(), name="home"),
        path("contact/", contact.as_view(), name="contact us"),
        path("all-products/", AllProductsView.as_view(), name="allproducts"),
        path("product/<slug:slug>/", ProductDetailView.as_view(), name="productdetail"),
        path("add-to-cart-<int:pro_id>/", AddToCartView.as_view(), name="addtocart"),
        path("my-cart/", MyCartView.as_view(), name="mycart"),
        path("manage-cart/<int:cp_id>/", ManageCartView.as_view(), name="managecart"),
        path("checkout/", CheckoutView.as_view(), name="checkout"),
        path("register/", CustomerRegistrationView.as_view(), name="customerregistration"),
        path("logout/", CustomerLogoutView.as_view(), name="customerlogout"),
        path("login/", CustomerLoginView.as_view(), name="customerlogin"),
        path("profile/", CustomerProfileView.as_view(), name="customerprofile"),
        path("profile/order-<int:pk>/", CustomerOrderDetailView.as_view(), name="customerorderdetail"),
        path("search/", SearchView.as_view(), name="search"),
        path("forgot-password/", PasswordForgotView.as_view(), name="passworforgot"),
        path("orderplace/", OrderplacedView.as_view(), name="orderplaced"),
        
        
        path("admin-login/", AdminLoginView.as_view(), name="adminlogin"),
        path("admin-home/", AdminHomeView.as_view(), name="adminhome"),
        path("admin-order/<int:pk>/", AdminOrderDetailView.as_view(),
         name="adminorderdetail"),

        path("admin-all-orders/", AdminOrderListView.as_view(), name="adminorderlist"),

        path("admin-order-<int:pk>-change/",
         AdminOrderStatuChangeView.as_view(), name="adminorderstatuschange"),

        path("admin-product/list/", AdminProductListView.as_view(),
         name="adminproductlist"),
        path("admin-product/add/", AdminProductCreateView.as_view(),
         name="adminproductcreate"),
        
        
        
        
        
        
        path("Delivery-login/", DeliveryLoginView.as_view(), name="Deliverylogin"),     
        path("delivery-all-orders/", DeliveryOrderListView.as_view(), name="DeliveryOrderList"),   
        path("delivery-order/<int:pk>/", DeliveryOrderDetailView.as_view(), name="DeliveryOrderDetail"),
        path("Deliverymanage/<int:dk>/", Deliverymanageview.as_view(), name="Deliverymanage"),
        path("pendingdelivery/", Currentdelivery.as_view(), name="Currentdelivery"),
        path("pending-delivery-order/<int:pk>/", pendingDeliveryOrderDetailView.as_view(), name="pendingDeliveryOrderDetail"),
        path("pending-order-<int:pk>-change/", pendingDeliveryOrderStatuChangeView.as_view(), name="pendingDeliveryOrderStatuChange"),
             


]
