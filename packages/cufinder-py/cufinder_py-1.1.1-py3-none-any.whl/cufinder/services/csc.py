from ..models.responses import CscResponse
from .base import BaseService


class Csc(BaseService):
    """
    CSC - Company Mission Statement API (V2)
    """

    def get_company_mission_statment(self, url: str) -> CscResponse:
        """
        Get company mission statement

        Args:
            url: The company domain you want to check
            
        Returns:
            CscResponse: Company mission statement
        """
        try:
            response = self.client.post("/csc", {
                "url": url.strip(),
            })

            return CscResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CSC Service")
