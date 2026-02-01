from typing import Dict, Optional, Union

from ..models.responses import LbsResponse
from ..types import LbsParams
from .base import BaseService


class Lbs(BaseService):
    """
    LBS - Local Business Search API (V2).
    """

    def search_local_businesses(self, params: Union[LbsParams, Dict, None] = None) -> LbsResponse:
        """
        Search for local businesses by location, industry, or name.
        
        Args:
            params: LBS V2 parameters (dict or LbsParams object)
            
        Returns:
            LbsResponse: Local business search results with companies list
        """
        try:
            if params is None:
                search_params = {}
            elif isinstance(params, dict):
                search_params = params
            else:
                search_params = params.to_dict()

            response = self.client.post("/lbs", search_params)

            return LbsResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "LBS Service")
