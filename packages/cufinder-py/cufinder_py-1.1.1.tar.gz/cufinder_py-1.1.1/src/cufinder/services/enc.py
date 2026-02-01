from ..models.responses import EncResponse
from .base import BaseService


class Enc(BaseService):
    """
    ENC - Company Enrichment API (V2).
    """

    def enrich_company(self, query: str) -> EncResponse:
        """
        Enriches company information from various data sources.
        
        Args:
            query: Company name or domain to enrich
            
        Returns:
            EncResponse: Enriched company information
        """

        try:
            response = self.client.post("/enc", {
                "query": query.strip(),
            })

            return EncResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "ENC Service")
