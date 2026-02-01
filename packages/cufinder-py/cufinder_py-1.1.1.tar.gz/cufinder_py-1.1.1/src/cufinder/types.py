"""API Service Parameter Types

These parameter type classes provide type-safe interfaces for all CUFinder search services.
They match the TypeScript SDK parameter interfaces exactly and include validation.

Available parameter types:
- CseParams: Company Search API parameters
- PseParams: Person Search API parameters  
- LbsParams: Local Business Search API parameters

Example usage:
    ```python
    from cufinder import Cufinder, CseParams, PseParams, LbsParams
    
    client = Cufinder('your-api-key-here')
    
    # Company search
    companies = client.cse(CseParams(name="tech", country="US"))
    
    # Person search
    people = client.pse(PseParams(full_name="John", company_name="Microsoft"))
    
    # Local business search
    businesses = client.lbs(LbsParams(city="New York", industry="food"))
    ```
"""

from typing import List, Optional


class CseParams:
    """
    CSE - Company Search API parameters.
    
    Provides type-safe parameters for the Company Search API (V2).
    All parameters are optional and can be combined for advanced filtering.
    
    Args:
        name: Company name to search for
        country: Country to filter by (e.g., 'US', 'United States')
        state: State/Province to filter by
        city: City to filter by
        followers_count_min: Minimum LinkedIn followers count
        followers_count_max: Maximum LinkedIn followers count
        industry: Industry to filter by
        employee_size: Employee size range (e.g., '1-10', '51-200', '10000+')
        founded_after_year: Founded after year
        founded_before_year: Founded before year
        funding_amount_max: Maximum funding amount
        funding_amount_min: Minimum funding amount
        products_services: List of products/services
        is_school: Filter for schools only
        annual_revenue_min: Minimum annual revenue
        annual_revenue_max: Maximum annual revenue
        page: Page number for pagination
        
    Example:
        ```python
        params = CseParams(
            name="technology",
            country="US",
            industry="software",
            employee_size="51-200",
            founded_after_year=2020,
            page=1
        )
        companies = client.cse(params)
        ```
    """
    def __init__(
        self,
        name: Optional[str] = None,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        followers_count_min: Optional[int] = None,
        followers_count_max: Optional[int] = None,
        industry: Optional[str] = None,
        employee_size: Optional[str] = None,
        founded_after_year: Optional[int] = None,
        founded_before_year: Optional[int] = None,
        funding_amount_max: Optional[int] = None,
        funding_amount_min: Optional[int] = None,
        products_services: Optional[List[str]] = None,
        is_school: Optional[bool] = None,
        annual_revenue_min: Optional[int] = None,
        annual_revenue_max: Optional[int] = None,
        page: Optional[int] = None,
    ):
        self.name = name
        self.country = country
        self.state = state
        self.city = city
        self.followers_count_min = followers_count_min
        self.followers_count_max = followers_count_max
        self.industry = industry
        self.employee_size = employee_size
        self.founded_after_year = founded_after_year
        self.founded_before_year = founded_before_year
        self.funding_amount_max = funding_amount_max
        self.funding_amount_min = funding_amount_min
        self.products_services = products_services
        self.is_school = is_school
        self.annual_revenue_min = annual_revenue_min
        self.annual_revenue_max = annual_revenue_max
        self.page = page

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class PseParams:
    """
    PSE - Person Search API parameters.
    
    Provides type-safe parameters for the Person Search API (V2).
    All parameters are optional and can be combined for advanced filtering.
    
    Args:
        full_name: Full name to search for
        country: Country to filter by
        state: State/Province to filter by
        city: City to filter by
        job_title_role: Job title role to filter by
        job_title_level: Job title level to filter by
        company_country: Company country to filter by
        company_state: Company state to filter by
        company_city: Company city to filter by
        company_name: Company name to filter by
        company_linkedin_url: Company LinkedIn URL to filter by
        company_industry: Company industry to filter by
        company_employee_size: Company employee size to filter by
        company_products_services: Company products/services to filter by
        company_annual_revenue_min: Company minimum annual revenue
        company_annual_revenue_max: Company maximum annual revenue
        page: Page number for pagination
        
    Example:
        ```python
        params = PseParams(
            full_name="John Smith",
            company_name="Microsoft",
            job_title_role="Engineer",
            country="US",
            page=1
        )
        people = client.pse(params)
        ```
    """
    def __init__(
        self,
        full_name: Optional[str] = None,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        job_title_role: Optional[str] = None,
        job_title_level: Optional[str] = None,
        company_country: Optional[str] = None,
        company_state: Optional[str] = None,
        company_city: Optional[str] = None,
        company_name: Optional[str] = None,
        company_linkedin_url: Optional[str] = None,
        company_industry: Optional[str] = None,
        company_employee_size: Optional[str] = None,
        company_products_services: Optional[List[str]] = None,
        company_annual_revenue_min: Optional[int] = None,
        company_annual_revenue_max: Optional[int] = None,
        page: Optional[int] = None,
    ):
        self.full_name = full_name
        self.country = country
        self.state = state
        self.city = city
        self.job_title_role = job_title_role
        self.job_title_level = job_title_level
        self.company_country = company_country
        self.company_state = company_state
        self.company_city = company_city
        self.company_name = company_name
        self.company_linkedin_url = company_linkedin_url
        self.company_industry = company_industry
        self.company_employee_size = company_employee_size
        self.company_products_services = company_products_services
        self.company_annual_revenue_min = company_annual_revenue_min
        self.company_annual_revenue_max = company_annual_revenue_max
        self.page = page

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


class LbsParams:
    """
    LBS - Local Business Search API parameters.
    
    Provides type-safe parameters for the Local Business Search API (V2).
    All parameters are optional and can be combined for advanced filtering.
    
    Args:
        name: Business name to search for
        country: Country to search in
        state: State/Province to search in
        city: City to search in
        industry: Industry to filter by
        page: Page number for pagination
        
    Example:
        ```python
        params = LbsParams(
            name="restaurant",
            country="United States",
            state="New York",
            city="New York",
            industry="food",
            page=1
        )
        businesses = client.lbs(params)
        ```
    """
    def __init__(
        self,
        name: Optional[str] = None,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        industry: Optional[str] = None,
        page: Optional[int] = None,
    ):
        self.name = name
        self.country = country
        self.state = state
        self.city = city
        self.industry = industry
        self.page = page

    def to_dict(self) -> dict:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in self.__dict__.items() if v is not None}
