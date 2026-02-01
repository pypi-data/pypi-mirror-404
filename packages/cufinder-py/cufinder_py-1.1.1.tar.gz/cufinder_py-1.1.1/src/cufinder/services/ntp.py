from ..models.responses import NtpResponse
from .base import BaseService


class Ntp(BaseService):
    """
    NTP - Company Phone Finder API (V2).
    """

    def get_phones(self, company_name: str) -> NtpResponse:
        """
        Returns up to two verified phone numbers for a company.
        
        Args:
            company_name: The name of the company to find phones for
            
        Returns:
            NtpResponse: Company phone information
        """

        try:
            response = self.client.post("/ntp", {
                "company_name": company_name.strip(),
            })

            return NtpResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "NTP Service")
