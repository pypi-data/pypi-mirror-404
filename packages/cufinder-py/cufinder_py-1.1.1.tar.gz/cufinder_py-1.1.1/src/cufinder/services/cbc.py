from ..models.responses import CbcResponse
from .base import BaseService


class Cbc(BaseService):
    """
    CBC - Company B2B or B2C Checker API (V2)
    """

    def get_company_business_type(self, url: str) -> CbcResponse:
        """
        Get company business type

        Args:
            url: The company domain you want to check is saas or not
            
        Returns:
            CbcResponse: yes or no
        """
        try:
            response = self.client.post("/cbc", {
                "url": url.strip(),
            })

            return CbcResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CBC Service")
