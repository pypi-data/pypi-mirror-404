"""
Cufinder Python SDK - Type-safe Python SDK for the Cufinder B2B Data Enrichment API

Example:
    ```python
    from cufinder import Cufinder
    
    client = Cufinder('your-api-key-here')
    
    # API usage
    result = client.cuf('cufinder', 'US')
    print(result)
    
    result = client.tep('iain mckenzie', 'stripe')
    print(result)
    ```
"""

from .client import CufinderClient
from .sdk import Cufinder
from .base_api_client import BaseApiClient, CufinderClientConfig, RequestConfig, Response
from .exceptions import (
    CufinderError,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    CreditLimitError,
    NetworkError,
    NotFoundError,
    PayloadError,
    ServerError,
)
from .models import *
from .services import *
from .types import CseParams, PseParams, LbsParams

__version__ = "1.1.1"
__author__ = "CUFinder Team"
__email__ = "support@cufinder.io"

# SDK metadata
SDK_INFO = {
    "name": "cufinder-py",
    "version": __version__,
    "description": "A Python SDK for the CUFinder API that provides access to all company and person enrichment services.",
    "homepage": "https://github.com/cufinder/cufinder-py",
    "repository": "https://github.com/cufinder/cufinder-py.git",
    "author": __author__,
    "license": "MIT",
}

__all__ = [
    "Cufinder",
    "CufinderClient",
    "BaseApiClient",
    "CufinderClientConfig",
    "RequestConfig",
    "Response",
    "CufinderError",
    "AuthenticationError",
    "ValidationError",
    "RateLimitError",
    "CreditLimitError",
    "NetworkError",
    "NotFoundError",
    "PayloadError",
    "ServerError",
    # Models
    "BaseModel",
    "Company",
    "Person",
    "CufResponse",
    "EppResponse", 
    "LbsResponse",
    "DtcResponse",
    "DteResponse",
    "NtpResponse",
    "RelResponse",
    "FclResponse",
    "ElfResponse",
    "CarResponse",
    "FccResponse",
    "FtsResponse",
    "FweResponse",
    "TepResponse",
    "EncResponse",
    "CecResponse",
    "CloResponse",
    "CseResponse",
    "PseResponse",
    "LcufResponse",
    "BcdResponse",
    "CcpResponse",
    "IscResponse",
    "CbcResponse",
    "CscResponse",
    "CsnResponse",
    "NaoResponse",
    "NaaResponse",
    # Services
    "BaseService",
    "Cuf",
    "Epp", 
    "Lbs",
    "Dtc",
    "Dte",
    "Ntp",
    "Rel",
    "Fcl",
    "Elf",
    "Car",
    "Fcc",
    "Fts",
    "Fwe",
    "Tep",
    "Enc",
    "Cec",
    "Clo",
    "Cse",
    "Pse",
    "Lcuf",
    "Bcd",
    "Ccp",
    "Isc",
    "Cbc",
    "Csc",
    "Csn",
    "Nao",
    "Naa",
    # Types
    "CseParams",
    "PseParams", 
    "LbsParams",
    "__version__",
    "SDK_INFO",
]
