from ..models.responses import IscResponse
from .base import BaseService


class Isc(BaseService):
    """
    ISC - Company Saas Checker API (V2)
    """

    def is_saas(self, url: str) -> IscResponse:
        """
        Checks company you want to know is saas or not
        
        Args:
            url: The company domain you want to check is saas or not
            
        Returns:
            IscResponse: yes or no
        """
        try:
            response = self.client.post("/isc", {
                "url": url.strip(),
            })

            return IscResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "ISC Service")
