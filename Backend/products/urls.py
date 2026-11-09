from django.urls import path

from .views import ProductCategoryListView, ProductDetailView, ProductImportView, ProductListCreateView

app_name = "products"

urlpatterns = [
    path("", ProductListCreateView.as_view(), name="list"),
    path("categories/", ProductCategoryListView.as_view(), name="categories"),
    path("import/", ProductImportView.as_view(), name="import"),
    path("<int:pk>/", ProductDetailView.as_view(), name="detail"),
]
