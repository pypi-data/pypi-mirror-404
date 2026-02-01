"""Person-related data models."""

from typing import List, Optional

from .base import BaseModel


class Person(BaseModel):
    """Person data model"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    summary: Optional[str] = None
    followers_count: Optional[int] = None
    facebook: Optional[str] = None
    twitter: Optional[str] = None
    avatar: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    job_title: Optional[str] = None
    job_title_categories: Optional[List[str]] = None
    company_name: Optional[str] = None
    company_linkedin: Optional[str] = None
    company_website: Optional[str] = None
    company_size: Optional[str] = None
    company_industry: Optional[str] = None
    company_facebook: Optional[str] = None
    company_twitter: Optional[str] = None
    company_country: Optional[str] = None
    company_state: Optional[str] = None
    company_city: Optional[str] = None


class PeopleCompany(BaseModel):
    """People company model"""
    id: Optional[str] = None
    name: Optional[str] = None
    website: Optional[str] = None
    size: Optional[str] = None
    industry: Optional[str] = None
    main_location: Optional[dict] = None
    social: Optional[dict] = None


class PeopleLocation(BaseModel):
    """People location model"""
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None


class JobTitleCategory(BaseModel):
    """Job title category model"""
    category: str
    super_category: str


class PeopleCurrentJob(BaseModel):
    """People current job model"""
    title: Optional[str] = None
    role: Optional[str] = None
    level: Optional[str] = None
    categories: Optional[List[JobTitleCategory]] = None


class PeopleConnections(BaseModel):
    """People connections model"""
    has_work_email: Optional[bool] = None
    has_personal_email: Optional[bool] = None
    has_phone: Optional[bool] = None
    work_email: Optional[str] = None
    personal_email: Optional[str] = None
    phone: Optional[str] = None
    is_accept_all: Optional[bool] = None
    is_accept_email: Optional[bool] = None


class PeopleSocial(BaseModel):
    """People social model"""
    linkedin_username: Optional[str] = None
    linkedin_connections: Optional[int] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    facebook: Optional[str] = None
    github: Optional[str] = None


class ExperienceCompany(BaseModel):
    """Experience company model"""
    name: Optional[str] = None
    size: Optional[str] = None
    id: Optional[str] = None
    founded: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    linkedin_id: Optional[str] = None
    facebook_url: Optional[str] = None
    twitter_url: Optional[str] = None
    website: Optional[str] = None
    job_company_id_mongo: Optional[str] = None


class PeopleExperience(BaseModel):
    """People experience model"""
    company: Optional[ExperienceCompany] = None
    location_names: Optional[List[str]] = None
    end_date: Optional[str] = None
    start_date: Optional[str] = None
    title: Optional[dict] = None
    is_primary: Optional[bool] = None
    summary: Optional[str] = None


class PeopleEducation(BaseModel):
    """People education model"""
    school: Optional[dict] = None
    end_date: Optional[str] = None
    start_date: Optional[str] = None
    gpa: Optional[str] = None
    degrees: Optional[List[str]] = None
    majors: Optional[List[str]] = None
    minors: Optional[List[str]] = None
    summary: Optional[str] = None


class PeopleCertification(BaseModel):
    """People certification model"""
    organization: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    name: Optional[str] = None


class PersonSearchResult(BaseModel):
    """Person search result model"""
    full_name: Optional[str] = None
    current_job: Optional[dict] = None
    company: Optional[dict] = None
    location: Optional[dict] = None
    social: Optional[dict] = None


class WorkExperience(BaseModel):
    """Work experience model"""
    company: str
    title: str
    start_date: str
    end_date: str
    current: bool


class Education(BaseModel):
    """Education model"""
    school: str
    degree: str
    field_of_study: str
    graduation_year: int


class TepPerson(Person):
    """TEP Person extends Person with email and phone"""
    email: Optional[str] = None
    phone: Optional[str] = None