from ..models.responses import FweResponse
from .base import BaseService


class Fwe(BaseService):
    """
    FWE - Email from Profile API (V2).
    """

    def get_email_from_profile(self, profile_url: str) -> FweResponse:
        """
        Extracts email addresses from social media profiles.
        
        Args:
            profile_url: Social media profile URL to extract email from
            
        Returns:
            FweResponse: Email information
        """
        try:
            response = self.client.post("/fwe", {
                "linkedin_url": profile_url.strip(),
            })

            return FweResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "FWE Service")
