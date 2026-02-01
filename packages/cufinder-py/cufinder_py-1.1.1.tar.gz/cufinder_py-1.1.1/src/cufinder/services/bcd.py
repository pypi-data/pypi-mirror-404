from ..models.responses import BcdResponse
from .base import BaseService


class Bcd(BaseService):
    """
    BCD - B2B Customers Finder API (V2).
    """

    def get_b2b_customers(self, url: str) -> BcdResponse:
        """  
        Extract B2B Customers From the Domain.

        Args:
            url: The domain to extract B2B customers for
            
        Returns:
            BcdResponse: Customers list
        """
        try:
            response = self.client.post("/bcd", {
                "url": url.strip(),
            })

            return BcdResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "BCD Service")
