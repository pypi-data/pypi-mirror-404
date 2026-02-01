from ..models.responses import LcufResponse
from .base import BaseService


class Lcuf(BaseService):
    """
    LCUF - LinkedIn Company URL Finder API (V2).
    """

    def get_linkedin_url(self, company_name: str) -> LcufResponse:
        """
        Finds LinkedIn company URLs from company names.
        
        Args:
            company_name: The name of the company to find LinkedIn URL for
            
        Returns:
            LcufResponse: LinkedIn URL information
        """

        try:
            response = self.client.post("/lcuf", {
                "company_name": company_name.strip(),
            })

            return LcufResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "LCUF Service")
