from ..models.responses import DteResponse
from .base import BaseService


class Dte(BaseService):
    """
    DTE - Company Email Finder API (V2).
    """

    def get_emails(self, company_website: str) -> DteResponse:
        """
        Finds company emails by domain
        
        Args:
            company_website: The website URL to find emails for
            
        Returns:
            DteResponse: Company email information
        """
        try:
            response = self.client.post("/dte", {
                "company_website": company_website.strip(),
            })

            return DteResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "DTE Service")


__all__ = ["Dte"]
