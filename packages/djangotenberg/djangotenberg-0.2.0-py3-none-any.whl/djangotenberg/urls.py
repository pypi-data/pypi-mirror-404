from django.urls import path
from .views import PDFView

urlpatterns = [
    path("pdf-engine/", PDFView.as_view(), name="pdf-engine"),
]