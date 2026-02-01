from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from djangotenberg.retry import retry
from djangotenberg.client import APIClient
from djangotenberg.views.base import BaseAPIView

class PDFView(BaseAPIView):
    """
    API View สำหรับจัดการไฟล์ PDF
    """
    client = APIClient()

    def healthly(self):
        try:
            resp = retry(self.client.health, delay=1, retries=3)
        except Exception as e:
            return Response(
                {"error": "Gotenberg service is not available", "detail": str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if resp.json().get("status") != "up":
            return Response(
                {"error": "Gotenberg service is not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return True

    @action(detail=False, methods=["POST"], url_path='html-to-pdf', name='html-to-pdf')
    def html_to_pdf(self, request):
        html_string = request.data.get("html")
        if not html_string:
            return Response(
                {"error": "HTML string is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        properties = request.data.get("properties", None)
        
        if not self.healthly():
            return self.healthly()
        
        resp = self.client.html_to_pdf(html_string, properties)
        if not resp.ok:
            return Response(
                {"error": "Failed to convert HTML to PDF", "detail": resp.text},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(resp.content, status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], url_path='read-metadata', name='read-metadata')
    def read_metadata(self, request):
        pdf_files = request.data.get("pdf_files")
        if not pdf_files:
            return Response(
                {"error": "PDF files are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for pdf_file in pdf_files:
            if not pdf_file.get("data"):
                return Response(
                    {"error": "File data is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            data = pdf_file.get("data")
            if not isinstance(data, bytes):
                data = data.encode("utf-8")
            pdf_file["data"] = data
        
        if not self.healthly():
            return self.healthly()
        
        resp = self.client.read_pdf_metadata(pdf_files)
        if not resp.ok:
            return Response(
                {"error": "Failed to read PDF metadata", "detail": resp.text},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(resp.json(), status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], url_path='write-metadata', name='write-metadata')
    def write_metadata(self, request):
        pdf_files = request.data.get("pdf_files")
        if not pdf_files:
            return Response(
                {"error": "PDF files are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        metadata = request.data.get("metadata")
        if not metadata:
            return Response(
                {"error": "Metadata is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        for pdf_file in pdf_files:
            if not pdf_file.get("data"):
                return Response(
                    {"error": "File data is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            data = pdf_file.get("data")
            if not isinstance(data, bytes):
                data = data.encode("utf-8")
            pdf_file["data"] = data
        
        if not self.healthly():
            return self.healthly()
        
        resp = self.client.write_pdf_metadata(pdf_files, metadata)
        if not resp.ok:
            return Response(
                {"error": "Failed to write PDF metadata", "detail": resp.text},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return HttpResponse(
            resp.content, 
            status=status.HTTP_200_OK,
            content_type="application/pdf"
        )
        
    @action(detail=False, methods=["POST"], url_path='merge', name='merge')
    def merge(self, request):
        pdf_files = request.data.get("pdf_files")
        if not pdf_files:
            return Response(
                {"error": "PDF files are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        for pdf_file in pdf_files:
            if not pdf_file.get("data"):
                return Response(
                    {"error": "File data is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            data = pdf_file.get("data")
            if not isinstance(data, bytes):
                data = data.encode("utf-8")
            pdf_file["data"] = data
        
        metadata = request.data.get("metadata", None)
        
        if not self.healthly():
            return self.healthly()
        
        resp = self.client.merge_pdf(pdf_files, metadata)
        if not resp.ok:
            return Response(
                {"error": "Failed to merge PDF", "detail": resp.text},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return HttpResponse(
            resp.content, 
            status=status.HTTP_200_OK,
            content_type="application/pdf"
        )