"""Tests for the Cufinder models."""

import pytest
from cufinder.models import (
    BaseModel, Company, Person, CufResponse, EppResponse, LbsResponse,
    DtcResponse, DteResponse, NtpResponse, RelResponse, FclResponse,
    ElfResponse, CarResponse, FccResponse, FtsResponse, FweResponse,
    TepResponse, EncResponse, CecResponse, CloResponse, CseResponse,
    PseResponse, LcufResponse
)


class TestBaseModel:
    """Test cases for BaseModel."""

    def test_to_dict(self):
        """Test converting model to dictionary."""
        model = BaseModel()
        result = model.to_dict()
        assert isinstance(result, dict)

    def test_from_dict(self):
        """Test creating model from dictionary."""
        data = {"test": "value"}
        model = BaseModel.from_dict(data)
        assert isinstance(model, BaseModel)


class TestCompany:
    """Test cases for Company model."""

    def test_company_creation(self):
        """Test creating a company model."""
        company = Company(
            name="TechCorp",
            domain="techcorp.com",
            industry="Technology",
            size="100-500"
        )
        assert company.name == "TechCorp"
        assert company.domain == "techcorp.com"
        assert company.industry == "Technology"
        assert company.size == "100-500"

    def test_company_to_dict(self):
        """Test converting company to dictionary."""
        company = Company(name="TechCorp", domain="techcorp.com")
        result = company.to_dict()
        assert result["name"] == "TechCorp"
        assert result["domain"] == "techcorp.com"


class TestPerson:
    """Test cases for Person model."""

    def test_person_creation(self):
        """Test creating a person model."""
        person = Person(
            first_name="John",
            last_name="Doe",
            full_name="John Doe",
            email="john@example.com",
            job_title="Software Engineer"
        )
        assert person.first_name == "John"
        assert person.last_name == "Doe"
        assert person.full_name == "John Doe"
        assert person.email == "john@example.com"
        assert person.job_title == "Software Engineer"

    def test_person_to_dict(self):
        """Test converting person to dictionary."""
        person = Person(full_name="John Doe", email="john@example.com")
        result = person.to_dict()
        assert result["full_name"] == "John Doe"
        assert result["email"] == "john@example.com"


class TestCufResponse:
    """Test cases for CufResponse model."""

    def test_cuf_response_creation(self):
        """Test creating a CUF response model."""
        response = CufResponse(
            domain="techcorp.com",
            company_name="TechCorp",
            country_code="US",
            confidence=0.95
        )
        assert response.domain == "techcorp.com"
        assert response.company_name == "TechCorp"
        assert response.country_code == "US"
        assert response.confidence == 0.95

    def test_cuf_response_from_dict(self):
        """Test creating CUF response from dictionary."""
        data = {
            "domain": "techcorp.com",
            "company_name": "TechCorp",
            "confidence": 0.95
        }
        response = CufResponse.from_dict(data)
        assert response.domain == "techcorp.com"
        assert response.company_name == "TechCorp"
        assert response.confidence == 0.95


class TestEppResponse:
    """Test cases for EppResponse model."""

    def test_epp_response_creation(self):
        """Test creating an EPP response model."""
        person = Person(full_name="John Doe", job_title="Engineer")
        company = Company(name="TechCorp", domain="techcorp.com")
        
        response = EppResponse(
            person=person,
            company=company,
            linkedin_url="https://linkedin.com/in/johndoe",
            confidence=0.90
        )
        assert response.person.full_name == "John Doe"
        assert response.company.name == "TechCorp"
        assert response.linkedin_url == "https://linkedin.com/in/johndoe"
        assert response.confidence == 0.90


class TestLbsResponse:
    """Test cases for LbsResponse model."""

    def test_lbs_response_creation(self):
        """Test creating an LBS response model."""
        businesses = [
            {"name": "Coffee Shop", "address": "123 Main St"},
            {"name": "Restaurant", "address": "456 Oak Ave"}
        ]
        
        response = LbsResponse(
            companies=businesses,
            total=2,
            page=1,
            per_page=10
        )
        assert len(response.companies) == 2
        assert response.total == 2
        assert response.page == 1
        assert response.per_page == 10


class TestDteResponse:
    """Test cases for DteResponse model."""

    def test_dte_response_creation(self):
        """Test creating a DTE response model."""
        emails = ["contact@example.com", "info@example.com"]
        
        response = DteResponse(
            emails=emails,
            company_website="https://example.com",
            confidence=0.80
        )
        assert len(response.emails) == 2
        assert "contact@example.com" in response.emails
        assert response.company_website == "https://example.com"
        assert response.confidence == 0.80


class TestNtpResponse:
    """Test cases for NtpResponse model."""

    def test_ntp_response_creation(self):
        """Test creating an NTP response model."""
        phones = ["+1-555-123-4567", "+1-555-987-6543"]
        
        response = NtpResponse(
            phones=phones,
            company_name="TechCorp",
            confidence=0.75
        )
        assert len(response.phones) == 2
        assert "+1-555-123-4567" in response.phones
        assert response.company_name == "TechCorp"
        assert response.confidence == 0.75


class TestRelResponse:
    """Test cases for RelResponse model."""

    def test_rel_response_creation(self):
        """Test creating a REL response model."""
        person = Person(full_name="Jane Smith", email="jane@example.com")
        company = Company(name="Example Corp", domain="example.com")
        
        response = RelResponse(
            person=person,
            company=company,
            email="jane@example.com",
            confidence=0.88
        )
        assert response.person.full_name == "Jane Smith"
        assert response.company.name == "Example Corp"
        assert response.email == "jane@example.com"
        assert response.confidence == 0.88


class TestFclResponse:
    """Test cases for FclResponse model."""

    def test_fcl_response_creation(self):
        """Test creating an FCL response model."""
        lookalikes = [
            {"name": "SimilarCorp", "similarity": 0.85},
            {"name": "LikeCorp", "similarity": 0.78}
        ]
        
        response = FclResponse(
            companies=lookalikes,
            query="TechCorp",
            total=2
        )
        assert len(response.companies) == 2
        assert response.companies[0]["name"] == "SimilarCorp"
        assert response.query == "TechCorp"
        assert response.total == 2


class TestElfResponse:
    """Test cases for ElfResponse model."""

    def test_elf_response_creation(self):
        """Test creating an ELF response model."""
        fundraising = {
            "total_raised": "$10M",
            "rounds": ["Series A", "Series B"]
        }
        
        response = ElfResponse(
            fundraising=fundraising,
            query="TechCorp",
            confidence=0.82
        )
        assert response.fundraising["total_raised"] == "$10M"
        assert len(response.fundraising["rounds"]) == 2
        assert response.query == "TechCorp"
        assert response.confidence == 0.82


class TestCarResponse:
    """Test cases for CarResponse model."""

    def test_car_response_creation(self):
        """Test creating a CAR response model."""
        response = CarResponse(
            revenue="$50M - $100M",
            query="TechCorp",
            confidence=0.75
        )
        assert response.revenue == "$50M - $100M"
        assert response.query == "TechCorp"
        assert response.confidence == 0.75


class TestFccResponse:
    """Test cases for FccResponse model."""

    def test_fcc_response_creation(self):
        """Test creating an FCC response model."""
        subsidiaries = [
            {"name": "SubCorp1", "type": "subsidiary"},
            {"name": "SubCorp2", "type": "subsidiary"}
        ]
        
        response = FccResponse(
            subsidiaries=subsidiaries,
            query="Alphabet Inc",
            total=2
        )
        assert len(response.subsidiaries) == 2
        assert response.subsidiaries[0]["name"] == "SubCorp1"
        assert response.query == "Alphabet Inc"
        assert response.total == 2


class TestFtsResponse:
    """Test cases for FtsResponse model."""

    def test_fts_response_creation(self):
        """Test creating an FTS response model."""
        tech_stack = ["Python", "React", "AWS", "Docker"]
        
        response = FtsResponse(
            tech_stack=tech_stack,
            query="TechCorp",
            confidence=0.90
        )
        assert len(response.tech_stack) == 4
        assert "Python" in response.tech_stack
        assert "React" in response.tech_stack
        assert response.query == "TechCorp"
        assert response.confidence == 0.90


class TestFweResponse:
    """Test cases for FweResponse model."""

    def test_fwe_response_creation(self):
        """Test creating an FWE response model."""
        response = FweResponse(
            work_email="john.doe@example.com",
            profile_url="https://linkedin.com/in/johndoe",
            confidence=0.85
        )
        assert response.work_email == "john.doe@example.com"
        assert response.profile_url == "https://linkedin.com/in/johndoe"
        assert response.confidence == 0.85


class TestTepResponse:
    """Test cases for TepResponse model."""

    def test_tep_response_creation(self):
        """Test creating a TEP response model."""
        person = Person(
            full_name="John Doe",
            job_title="Software Engineer",
            company="TechCorp"
        )
        
        response = TepResponse(
            person=person,
            query="John Doe",
            confidence=0.88
        )
        assert response.person.full_name == "John Doe"
        assert response.person.job_title == "Software Engineer"
        assert response.person.company == "TechCorp"
        assert response.query == "John Doe"
        assert response.confidence == 0.88


class TestEncResponse:
    """Test cases for EncResponse model."""

    def test_enc_response_creation(self):
        """Test creating an ENC response model."""
        company = Company(
            name="TechCorp Inc",
            industry="Technology",
            size="100-500"
        )
        
        response = EncResponse(
            company=company,
            query="TechCorp",
            confidence=0.92
        )
        assert response.company.name == "TechCorp Inc"
        assert response.company.industry == "Technology"
        assert response.company.size == "100-500"
        assert response.query == "TechCorp"
        assert response.confidence == 0.92


class TestCecResponse:
    """Test cases for CecResponse model."""

    def test_cec_response_creation(self):
        """Test creating a CEC response model."""
        countries = ["United States", "Canada", "United Kingdom"]
        
        response = CecResponse(
            countries=countries,
            query="TechCorp",
            total=3
        )
        assert len(response.countries) == 3
        assert "United States" in response.countries
        assert "Canada" in response.countries
        assert response.query == "TechCorp"
        assert response.total == 3


class TestCloResponse:
    """Test cases for CloResponse model."""

    def test_clo_response_creation(self):
        """Test creating a CLO response model."""
        locations = [
            {"city": "San Francisco", "country": "USA"},
            {"city": "New York", "country": "USA"}
        ]
        
        response = CloResponse(
            locations=locations,
            query="TechCorp",
            total=2
        )
        assert len(response.locations) == 2
        assert response.locations[0]["city"] == "San Francisco"
        assert response.query == "TechCorp"
        assert response.total == 2


class TestCseResponse:
    """Test cases for CseResponse model."""

    def test_cse_response_creation(self):
        """Test creating a CSE response model."""
        companies = [
            {"name": "TechCorp", "industry": "Software"},
            {"name": "DataCorp", "industry": "Analytics"}
        ]
        
        response = CseResponse(
            companies=companies,
            total=2,
            page=1,
            per_page=10
        )
        assert len(response.companies) == 2
        assert response.companies[0]["name"] == "TechCorp"
        assert response.total == 2
        assert response.page == 1
        assert response.per_page == 10


class TestPseResponse:
    """Test cases for PseResponse model."""

    def test_pse_response_creation(self):
        """Test creating a PSE response model."""
        people = [
            {"name": "John Doe", "title": "Software Engineer"},
            {"name": "Jane Smith", "title": "Product Manager"}
        ]
        
        response = PseResponse(
            peoples=people,
            total=2,
            page=1,
            per_page=10
        )
        assert len(response.peoples) == 2
        assert response.peoples[0]["name"] == "John Doe"
        assert response.total == 2
        assert response.page == 1
        assert response.per_page == 10


class TestLcufResponse:
    """Test cases for LcufResponse model."""

    def test_lcuf_response_creation(self):
        """Test creating an LCUF response model."""
        response = LcufResponse(
            linkedin_url="https://linkedin.com/company/techcorp",
            company_name="TechCorp",
            confidence=0.95
        )
        assert response.linkedin_url == "https://linkedin.com/company/techcorp"
        assert response.company_name == "TechCorp"
        assert response.confidence == 0.95
