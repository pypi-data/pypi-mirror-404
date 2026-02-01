"""Company-related data models."""

from typing import List, Optional, Union
from .base import BaseModel


class Company(BaseModel):
    """Company data model"""
    name: Optional[str] = None
    website: Optional[str] = None
    employee_count: Optional[Union[str, int]] = None
    size: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    linkedin_url: Optional[str] = None
    type: Optional[str] = None
    domain: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    founded_year: Optional[str] = None
    logo_url: Optional[str] = None
    followers_count: Optional[int] = None


class CompanyLocation(BaseModel):
    """Company location model"""
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class CompanyTechnology(BaseModel):
    """Company technology model"""
    category: Optional[str] = None
    super_category: Optional[str] = None
    technology_name: Optional[str] = None
    technology_website: Optional[str] = None


class EnrichedCompany(BaseModel):
    """Enriched company model"""
    name: Optional[str] = None
    website: Optional[str] = None
    domain: Optional[str] = None
    logo: Optional[str] = None
    overview: Optional[str] = None
    founded_date: Optional[str] = None
    industry: Optional[str] = None
    annual_revenue: Optional[str] = None
    followers: Optional[int] = None
    is_school: Optional[bool] = None
    is_investor: Optional[bool] = None
    has_email: Optional[bool] = None
    has_phone: Optional[bool] = None
    suggesstions: Optional[List[str]] = None
    locations: Optional[List[CompanyLocation]] = None
    technologies: Optional[List[CompanyTechnology]] = None
    affiliated_pages: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    employees: Optional[dict] = None
    main_location: Optional[dict] = None
    geo_location: Optional[dict] = None
    industry_details: Optional[dict] = None
    funding: Optional[dict] = None
    social: Optional[dict] = None
    connections: Optional[dict] = None


class CompanySearchResult(BaseModel):
    """Company search result model"""
    name: Optional[str] = None
    website: Optional[str] = None
    domain: Optional[str] = None
    employees: Optional[dict] = None
    industry: Optional[str] = None
    overview: Optional[str] = None
    type: Optional[str] = None
    main_location: Optional[dict] = None
    social: Optional[dict] = None


class LocalBusinessResult(BaseModel):
    """Local business result model"""
    name: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    industry_details: Optional[dict] = None
    main_location: Optional[dict] = None
    geo_location: Optional[dict] = None
    social: Optional[dict] = None
    connections: Optional[dict] = None


class LookalikeCompany(BaseModel):
    """Lookalike company model"""
    name: Optional[str] = None
    website: Optional[str] = None
    employee_count: Optional[Union[str, int]] = None
    size: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    linkedin_url: Optional[str] = None
    type: Optional[str] = None
    domain: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    founded_year: Optional[str] = None
    logo_url: Optional[str] = None
    followers_count: Optional[int] = None


class FundraisingInfo(BaseModel):
    """Fundraising info model"""
    funding_last_round_type: Optional[str] = None
    funding_ammount_currency_code: Optional[str] = None
    funding_money_raised: Optional[str] = None
    funding_last_round_investors_url: Optional[str] = None


class CloCompanyLocation(BaseModel):
    """Company location for CLO response"""
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SnapshotModel(BaseModel):
    """Snapshot info model"""
    icp: str | None
    target_industries: List[str];
    target_personas: List[str];
    value_proposition: str | None
