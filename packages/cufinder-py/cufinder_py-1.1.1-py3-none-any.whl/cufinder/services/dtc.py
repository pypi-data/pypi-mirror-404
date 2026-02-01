from ..models.responses import DtcResponse
from .base import BaseService


class Dtc(BaseService):
    """
    DTC - Domain to Company Name API (V2).
    """

    def get_company_name(self, company_website: str) -> DtcResponse:
        """
        Retrieves the registered company name associated with a given website domain.
        
        Args:
            company_website: The website URL to lookup
            
        Returns:
            DtcResponse: Company name information
        """
        try:
            response = self.client.post("/dtc", {
                "company_website": company_website.strip(),
            })

            return DtcResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "DTC Service")
