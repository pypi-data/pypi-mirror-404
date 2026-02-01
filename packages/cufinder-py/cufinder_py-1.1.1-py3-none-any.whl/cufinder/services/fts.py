from ..models.responses import FtsResponse
from .base import BaseService


class Fts(BaseService):
    """
    FTS - Company Tech Stack Finder API (V2).
    """

    def get_tech_stack(self, query: str) -> FtsResponse:
        """
        Returns technology stack information for a company.
        
        Args:
            query: Company name or website to get tech stack for
            
        Returns:
            FtsResponse: Technology stack information
        """

        try:
            response = self.client.post("/fts", {
                "query": query.strip(),
            })

            return FtsResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "FTS Service")
