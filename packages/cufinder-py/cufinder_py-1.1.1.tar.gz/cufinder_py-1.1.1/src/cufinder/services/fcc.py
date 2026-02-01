from ..models.responses import FccResponse
from .base import BaseService


class Fcc(BaseService):
    """
    FCC - Company Subsidiaries Finder API (V2).
    """

    def get_subsidiaries(self, query: str) -> FccResponse:
        """
        Identifies known subsidiaries of a parent company.
        
        Args:
            query: Company name to find subsidiaries for
            
        Returns:
            FccResponse: Subsidiaries information
        """

        try:
            response = self.client.post("/fcc", {
                "query": query.strip(),
            })

            return FccResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "FCC Service")
