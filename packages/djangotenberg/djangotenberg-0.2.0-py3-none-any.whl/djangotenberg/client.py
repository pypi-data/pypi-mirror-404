import json

import requests

from .conf import get_config
from .exceptions import APIRequestError
from .properties.validate import validate_properties

class APIClient:
    def __init__(self):
        config: dict = get_config()
        self.base_url: str = config["GOTENBERG_URL"]
        self.timeout: int = config.get("GOTENBERG_API_TIMEOUT", 10)
        
    def _headers(self):
        headers = {"Content-Type": "application/json"}
        return headers
        
    def _get(self, path, params=None, headers=None):
        url = f"{self.base_url}{path}"
        
        if headers:
            headers.update(self._headers())
        else:
            headers = self._headers()

        resp = requests.get(url, headers=headers, 
                            params=params, timeout=self.timeout)
        if not resp.ok:
            raise APIRequestError(resp.text)
        
        return resp
    
    def _post(self, path, headers=None, files=None, params=None, data=None):
        url = f"{self.base_url}{path}"
        resp = requests.post(url, headers=headers,
                             data=data, timeout=self.timeout,
                             params=params, files=files)
        if not resp.ok:
            raise APIRequestError(resp.text)
        
        return resp

    def health(self):
        path = "/health"
        return self._get(path)

    def html_to_pdf(self, html_string, properties: dict = None):
        path = "/forms/chromium/convert/html"
        files = {
            'files': ('index.html', html_string, 'text/html')
        }

        if properties is not None and isinstance(properties, dict):
            validate_properties(properties)
        
        return self._post(path, files=files, data=properties)
    
    def read_pdf_metadata(self, pdf_files: list[dict]):
        path = "/forms/pdfengines/metadata/read"

        files = []
        for i, pdf_file in enumerate(pdf_files):
            if not pdf_file.get("file") or not pdf_file.get("data"):
                raise ValueError("File and data are required")
            
            file_name = pdf_file.get("file")
            data = pdf_file.get("data")
            files.append(("files", (file_name, data, "application/pdf")))
        
        return self._post(path, files=files)

    def write_pdf_metadata(self, pdf_files: list[dict], metadata: dict):
        path = "/forms/pdfengines/metadata/write"

        metadata = {
            "metadata": json.dumps(metadata),
        }

        files = []
        for i, pdf_file in enumerate(pdf_files):
            if not pdf_file.get("file") or not pdf_file.get("data"):
                raise ValueError("File and data are required")
            
            file_name = pdf_file.get("file")
            data = pdf_file.get("data")

            files.append(("files", (file_name, data, "application/pdf")))

        return self._post(path, files=files, data=metadata)

    def merge_pdf(self, pdf_files: list[dict], metadata: dict = None):
        path = "/forms/pdfengines/merge"

        files = []
        for i, pdf_file in enumerate(pdf_files):
            if not pdf_file.get("file") or not pdf_file.get("data"):
                raise ValueError("File and data are required")
            
            file_name = pdf_file.get("file")
            data = pdf_file.get("data")

            files.append(("files", (file_name, data, "application/pdf")))

        return self._post(path, files=files, data=metadata)