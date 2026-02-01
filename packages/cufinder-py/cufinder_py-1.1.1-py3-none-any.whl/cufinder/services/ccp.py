from ..models.responses import CcpResponse
from .base import BaseService


class Ccp(BaseService):
    """
    CCP - Company Career Page Finder API (V2)
    """

    def find_careers_page(self, url: str) -> CcpResponse:
        """
        Find companies careers page

        Args:
            url: The company domain you want to find it's career page
            
        Returns:
            CcpResponse: Company careers page
        """
        try:
            response = self.client.post("/ccp", {
                "url": url.strip(),
            })

            return CcpResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CCP Service")
