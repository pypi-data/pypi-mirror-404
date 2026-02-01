from ..models.responses import FclResponse
from .base import BaseService


class Fcl(BaseService):
    """
    FCL - Company Lookalikes Finder API (V2).
    """

    def get_lookalikes(self, query: str) -> FclResponse:
        """
        Provides a list of similar companies based on an input company's profile.
        
        Args:
            query: Company name or description to find similar companies for
            
        Returns:
            FclResponse: List of similar companies
        """

        try:
            response = self.client.post("/fcl", {
                "query": query.strip(),
            })

            return FclResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "FCL Service")
