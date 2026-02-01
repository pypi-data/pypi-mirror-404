from typing import Dict, Optional, Union

from ..models.responses import CseResponse
from ..types import CseParams
from .base import BaseService


class Cse(BaseService):
    """
    CSE - Company Search API (V2).
    """

    def search_companies(self, params: Union[CseParams, Dict, None] = None) -> CseResponse:
        """
        Search for companies based on various criteria.
        
        Args:
            params: CSE V2 parameters object containing search criteria
            
        Returns:
            CseResponse: Company search results with list of companies
            
        Raises:
            ValidationError: If parameters are invalid
            AuthenticationError: If API key is invalid
            CreditLimitError: If not enough credits
            NetworkError: If network issues occur
            
        Example:
            ```python
            # Search for technology companies
            result = client.cse(
                name="technology",
                country="germany",
                industry="software",
                employee_size="51-200",
                page=1
            )
            print(f"Found {len(result.companies)} companies")
            
            # Access individual company data
            for company in result.companies:
                print(f"Company: {company.name}")
                print(f"Website: {company.website}")
                print(f"Industry: {company.industry}")
            ```
        """
        try:
            if params is None:
                search_params = {}
            elif isinstance(params, dict):
                search_params = params
            else:
                search_params = params.to_dict()

            response = self.client.post("/cse", search_params)

            return CseResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CSE Service")
