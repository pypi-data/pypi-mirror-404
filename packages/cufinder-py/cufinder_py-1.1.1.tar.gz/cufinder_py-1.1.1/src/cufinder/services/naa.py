from ..models.responses import NaaResponse
from .base import BaseService


class Naa(BaseService):
    """
    NAA - Address Normalizer API (V2)
    """

    def normalize_address(self, address: str) -> NaaResponse:
        """
        Args:
            address: The address you want to normalize
            
        Returns:
            NaaResponse: Normalized address
            
        Example:
            ```python
            result = client.nao("1095 avenue of the Americas, 6th Avenue ny 10036")
            print(result)
            ```
        """
        try:
            response = self.client.post("/naa", {
                "address": address.strip(),
            })

            return NaaResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "NAA Service")
