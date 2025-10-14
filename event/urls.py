from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter
from .views import TicketPDFView
from .views import ApplyPromoAPIView
from .views import ReviewListCreateAPIView
from .views import wallet_balance 
from .views import AddBalanceAPIView 

router = DefaultRouter()
router.register('events', views.EventViewSet, basename='events')
router.register('ticket', views.TicketViewSet, basename='ticket')
router.register('category', views.CategoryViewSet, basename='category')
router.register('promocode', views.PromoCodeViewSet, basename='promocode')

urlpatterns = [
    path('health_check/', views.HealthCheckAPIView.as_view()),
    path('order-items/', views.OrderItemAPIView.as_view()),
    path('orders/', views.OrderAPIView.as_view()),
    path('orders/<int:pk>/', views.OrderAPIView.as_view()),
    path('ticket/<int:pk>/pdf/', TicketPDFView.as_view(), name='ticket-pdf'),
    path('orders/<int:pk>/apply_promo/', ApplyPromoAPIView.as_view()),
    path('reviews/', ReviewListCreateAPIView.as_view(), name='reviews'),
    path('wallet/balance/', wallet_balance, name='wallet-balance'),
    path('wallet/add-balance/', AddBalanceAPIView.as_view(), name='add-balance'),
] 

urlpatterns += router.urls