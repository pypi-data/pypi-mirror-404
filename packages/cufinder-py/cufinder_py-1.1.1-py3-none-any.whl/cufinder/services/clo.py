from ..models.responses import CloResponse
from .base import BaseService


class Clo(BaseService):
    """
    CLO - Company Locations API (V2).
    """

    def get_locations(self, query: str) -> CloResponse:
        """
        Returns office locations for a company.
        
        Args:
            query: Company name to get locations for
            
        Returns:
            CloResponse: Company locations information
        """

        try:
            response = self.client.post("/clo", {
                "query": query.strip(),
            })

            return CloResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CLO Service")
