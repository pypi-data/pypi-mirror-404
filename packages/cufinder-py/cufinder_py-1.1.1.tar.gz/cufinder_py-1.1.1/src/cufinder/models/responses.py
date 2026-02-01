"""API response models."""

from typing import List, Optional, Union

from .base import BaseResponse
from .company import Company, CompanySearchResult, LocalBusinessResult, LookalikeCompany, FundraisingInfo, CloCompanyLocation, SnapshotModel
from .person import Person, PersonSearchResult, TepPerson


class CufResponse(BaseResponse):
    """CUF Response - Company Name to Domain"""
    domain: str


class LcufResponse(BaseResponse):
    """LCUF Response - Company LinkedIn URL Finder"""
    linkedin_url: str


class DtcResponse(BaseResponse):
    """DTC Response - Domain to Company Name"""
    company_name: str


class DteResponse(BaseResponse):
    """DTE Response - Company Email Finder"""
    emails: List[str]


class NtpResponse(BaseResponse):
    """NTP Response - Company Phone Finder"""
    phones: List[str]


class RelResponse(BaseResponse):
    """REL Response - Reverse Email Lookup"""
    person: Person


class FclResponse(BaseResponse):
    """FCL Response - Company Lookalikes Finder"""
    companies: List[LookalikeCompany]


class ElfResponse(BaseResponse):
    """ELF Response - Company Fundraising API"""
    fundraising_info: FundraisingInfo


class CarResponse(BaseResponse):
    """CAR Response - Company Revenue Finder"""
    annual_revenue: str


class FccResponse(BaseResponse):
    """FCC Response - Company Subsidiaries Finder"""
    subsidiaries: List[str]


class FtsResponse(BaseResponse):
    """FTS Response - Company Tech Stack Finder"""
    technologies: List[str]


class EppResponse(BaseResponse):
    """EPP Response - LinkedIn Profile Enrichment"""
    person: Person


class FweResponse(BaseResponse):
    """FWE Response - LinkedIn Profile Email Finder"""
    work_email: str


class TepResponse(BaseResponse):
    """TEP Response - Person Enrichment"""
    person: TepPerson


class EncResponse(BaseResponse):
    """ENC Response - Company Enrichment"""
    company: Company


class CecResponse(BaseResponse):
    """CEC Response - Company Employees Countries"""
    countries: Union[dict, list]


class CloResponse(BaseResponse):
    """CLO Response - Company Locations"""
    locations: List[CloCompanyLocation]


class CseResponse(BaseResponse):
    """CSE Response - Company Search"""
    companies: List[CompanySearchResult]


class PseResponse(BaseResponse):
    """PSE Response - Person Search"""
    peoples: List[PersonSearchResult]


class LbsResponse(BaseResponse):
    """LBS Response - Local Business Search"""
    companies: List[LocalBusinessResult]


class BcdResponse(BaseResponse):
    """BCD Response - Extract B2B Customers From the Domain"""
    customers: List[str]


class CcpResponse(BaseResponse):
    careers_page_url: str | None


class IscResponse(BaseResponse):
    is_saas: str


class CbcResponse(BaseResponse):
    business_type: str


class CscResponse(BaseResponse):
    mission_statement: str | None


class CsnResponse(BaseResponse):
    company_snapshot: SnapshotModel


class NaoResponse(BaseResponse):
    phone: str


class NaaResponse(BaseResponse):
    address: str