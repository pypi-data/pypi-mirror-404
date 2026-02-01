from ..models.responses import CsnResponse
from .base import BaseService


class Csn(BaseService):
    """
    CSN - Company Snapshot API (V2)
    """

    def get_company_snapshot(self, url: str) -> CsnResponse:
        """
        Get company snapshot info
        
        Args:
            url: The company domain you want to check
            
        Returns:
            CsnResponse: Company mission statement
        """
        try:
            response = self.client.post("/csn", {
                "url": url.strip(),
            })

            return CsnResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CSN Service")
