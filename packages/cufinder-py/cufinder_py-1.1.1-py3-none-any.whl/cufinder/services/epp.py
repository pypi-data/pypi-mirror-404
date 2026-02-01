from ..models.responses import EppResponse
from .base import BaseService


class Epp(BaseService):
    """
    EPP - LinkedIn Profile Enrichment API (V2).
    """

    def enrich_profile(self, linkedin_url: str) -> EppResponse:
        """
        Enrichs LinkedIn profile with detailed person and company information.
        
        Args:
            linkedin_url: The LinkedIn profile URL to enrich (e.g., 'linkedin.com/in/johndoe')
            
        Returns:
            EppResponse: Enriched person and company data including job title, company info, location, and social profiles
        """
        try:
            response = self.client.post("/epp", {
                "linkedin_url": linkedin_url.strip(),
            })

            return EppResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "EPP Service")
