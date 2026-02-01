from typing import Dict, Union

from ..models.responses import PseResponse
from ..types import PseParams
from .base import BaseService


class Pse(BaseService):
    """
    PSE - People Search API (V2).
    """

    def search_people(self, params: Union[PseParams, Dict, None] = None) -> PseResponse:
        """
        Search for people based on various criteria.
        
        Args:
            params: PSE V2 parameters including:
                - full_name: Full name to search for (optional)
                - country: Country to filter by (optional)
                - state: State/Province to filter by (optional)
                - city: City to filter by (optional)
                - job_title_role: Job title role to filter by (optional)
                - job_title_level: Job title level to filter by (optional)
                - company_name: Company name to filter by (optional)
                - company_linkedin_url: Company LinkedIn URL to filter by (optional)
                - company_industry: Company industry to filter by (optional)
                - company_employee_size: Company employee size to filter by (optional)
                - page: Page number for pagination (optional)
            
        Returns:
            PseResponse: People search results with peoples list
        """
        try:
            if params is None:
                search_params = {}
            elif isinstance(params, dict):
                search_params = params
            else:
                search_params = params.to_dict()

            response = self.client.post("/pse", search_params)

            return PseResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "PSE Service")
