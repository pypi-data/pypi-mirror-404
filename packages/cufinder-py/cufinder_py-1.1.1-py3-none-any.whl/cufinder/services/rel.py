from ..models.responses import RelResponse
from .base import BaseService


class Rel(BaseService):
    """
    REL - Reverse Email Lookup API (V2).
    """

    def reverse_email_lookup(self, email: str) -> RelResponse:
        """
        Enriches an email address with detailed person and company information.
        
        Args:
            email: The email address to lookup
            
        Returns:
            RelResponse: Person and company information
        """


        try:
            response = self.client.post("/rel", {
                "email": email.strip(),
            })

            return RelResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "REL Service")
