from abc import ABC, abstractmethod
from starlette.requests import Request
from starlette.responses import Response

class RequestHandlerInterface(ABC):
    """
    Interface for handling HTTP requests.
    """

    @abstractmethod
    async def handle_request(self, request: Request) -> Response:
        """
        Process the request and return a response.

        Args:
            request: The incoming HTTP request.
            
        Returns:
            The HTTP response.
        """
        ...
