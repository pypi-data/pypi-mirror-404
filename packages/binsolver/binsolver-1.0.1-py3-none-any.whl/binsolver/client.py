import httpx
from typing import Optional, Union, Dict, Any
from .models import PackRequest, PackResponse

class BinSolverError(Exception):
    """Base exception for BinSolver SDK"""
    pass

class ApiError(BinSolverError):
    """Exception raised for API error responses"""
    def __init__(self, status_code: int, message: str, code: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.code = code
        super().__init__(f"API Error {status_code}: {message} ({code})")

class BinSolver:
    """
    Client for the BinSolver API.
    
    Args:
        api_key (str): Your BinSolver API key.
        base_url (str, optional): API base URL. Defaults to "https://api.binsolver.com".
        timeout (float, optional): Request timeout in seconds. Defaults to 30.0.
    """
    def __init__(
        self, 
        api_key: str, 
        base_url: str = "https://api.binsolver.com",
        timeout: float = 30.0
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "User-Agent": "binsolver-python/0.1.0"
            },
            timeout=self.timeout
        )

    def health(self) -> bool:
        """
        Check if the API is healthy.
        
        Returns:
            bool: True if healthy, False otherwise.
        """
        try:
            response = self._client.get("/health")
            return response.status_code == 200 and response.text.strip() == "ok"
        except httpx.RequestError:
            return False

    def pack(self, request: Union[PackRequest, Dict[str, Any]]) -> PackResponse:
        """
        Pack items into bins.
        
        Args:
            request (PackRequest | dict): The packing request.
            
        Returns:
            PackResponse: The packing result.
            
        Raises:
            ApiError: If the API returns an error.
            httpx.RequestError: If the network request fails.
            pydantic.ValidationError: If the response is invalid.
        """
        if isinstance(request, PackRequest):
            payload = request.model_dump(by_alias=True, exclude_none=True)
        else:
            payload = request

        response = self._client.post("/v1/pack", json=payload)
        
        if not response.is_success:
            self._handle_error(response)
            
        return PackResponse.model_validate(response.json())

    def _handle_error(self, response: httpx.Response):
        try:
            data = response.json()
            error = data.get("error", {})
            message = error.get("message", response.text)
            code = error.get("code")
        except Exception:
            message = response.text
            code = None
            
        raise ApiError(response.status_code, message, code)
        
    def close(self):
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
