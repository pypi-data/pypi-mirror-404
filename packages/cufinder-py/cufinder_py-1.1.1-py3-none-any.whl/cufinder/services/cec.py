from ..models.responses import CecResponse
from .base import BaseService


class Cec(BaseService):
    """
    CEC - Company Employee Countries API (V2).
    """

    def get_employee_countries(self, query: str) -> CecResponse:
        """
        Returns countries where a company has employees.
        
        Args:
            query: Company name to get employee countries for
            
        Returns:
            CecResponse: Employee countries information
        """

        try:
            response = self.client.post("/cec", {
                "query": query.strip(),
            })

            return CecResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CEC Service")
