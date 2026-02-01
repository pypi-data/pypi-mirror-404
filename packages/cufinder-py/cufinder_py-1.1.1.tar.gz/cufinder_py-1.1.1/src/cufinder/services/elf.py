from ..models.responses import ElfResponse
from .base import BaseService


class Elf(BaseService):
    """
    ELF - Company Fundraising API (V2).
    """

    def get_fundraising(self, query: str) -> ElfResponse:
        """
        Returns detailed funding information about a company.
        
        Args:
            query: Company name to get fundraising data for
            
        Returns:
            ElfResponse: Fundraising information
        """

        try:
            response = self.client.post("/elf", {
                "query": query.strip(),
            })

            return ElfResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "ELF Service")
