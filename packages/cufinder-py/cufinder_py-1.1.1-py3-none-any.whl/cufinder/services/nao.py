from ..models.responses import NaoResponse
from .base import BaseService


class Nao(BaseService):
    """
    NAO - Phone Number Normalizer API (V2)
    """

    def normalize_phone(self, phone: str) -> NaoResponse:
        """
        Normalize phone number

        Args:
            phone: The phone number you want to normalize
            
        Returns:
            NaoResponse: Normalized phone
        """
        try:
            response = self.client.post("/nao", {
                "phone": phone.strip(),
            })

            return NaoResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "NAO Service")
