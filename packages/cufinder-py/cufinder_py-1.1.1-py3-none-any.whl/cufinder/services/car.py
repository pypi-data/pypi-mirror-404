from ..models.responses import CarResponse
from .base import BaseService


class Car(BaseService):
    """
    CAR - Company Revenue Finder API (V2).
    """

    def get_revenue(self, query: str) -> CarResponse:
        """
        Estimates a company's annual revenue based on name.
        
        Args:
            query: Company name to get revenue data for
            
        Returns:
            CarResponse: Revenue information
        """

        try:
            response = self.client.post("/car", {
                "query": query.strip(),
            })

            return CarResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CAR Service")
