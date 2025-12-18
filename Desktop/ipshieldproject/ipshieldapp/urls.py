from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # CUSTOMER
    path('customer-add/', views.add_customer, name='add_customer'),
    path('customer/<int:id>/', views.customer_detail, name='customer_detail'),
    path('customer/<int:id>/edit/', views.customer_edit, name='customer_edit'),
    path('customer/<int:id>/delete/', views.customer_delete, name='customer_delete'),

    # CONTRACT
    path("contracts/add/", views.add_contract, name="add_contract"),
    path("contracts/", views.contract_list, name="contract_list"),
    path("contracts/<int:id>/", views.contract_detail, name="contract_detail"),
    path('<int:pk>/change-status/', views.customer_change_status, name='customer_change_status'),
    path("contracts/edit/<int:id>", views.contract_edit, name="contract_edit"),
    path('api/search-customer/', views.search_customer, name='search_customer'),
    # CERTIFICATE (GIẤY CHỨNG NHẬN)
    path(
        'certificate/download/<int:id>/',
        views.download_certificate,
        name='download_certificate'
    ),

    #login.css
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

]
