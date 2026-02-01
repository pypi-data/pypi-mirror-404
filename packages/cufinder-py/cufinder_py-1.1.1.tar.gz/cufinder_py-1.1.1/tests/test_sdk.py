"""Tests for the Cufinder SDK."""

import pytest
from unittest.mock import Mock, patch

from cufinder import Cufinder
from cufinder.exceptions import ValidationError, AuthenticationError


class TestCufinder:
    """Test cases for Cufinder."""

    def test_init_with_valid_api_key(self):
        """Test SDK initialization with valid API key."""
        sdk = Cufinder(api_key="test-key")
        assert sdk.client.api_key == "test-key"
        assert sdk.client.base_url == "https://api.cufinder.io/v2"

    def test_init_with_custom_config(self):
        """Test SDK initialization with custom configuration."""
        sdk = Cufinder(
            api_key="test-key",
            base_url="https://custom.api.com",
            timeout=60,
            max_retries=5
        )
        assert sdk.client.base_url == "https://custom.api.com"
        assert sdk.client.timeout == 60
        assert sdk.client.max_retries == 5

    def test_get_client(self):
        """Test getting the underlying client."""
        sdk = Cufinder(api_key="test-key")
        client = sdk.get_client()
        assert client.api_key == "test-key"

    @patch('cufinder.client.requests.Session')
    def test_cuf_service(self, mock_session):
        """Test CUF service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "domain": "techcorp.com",
            "company_name": "TechCorp",
            "confidence": 0.95
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.cuf("TechCorp", "US")

        assert result.domain == "techcorp.com"
        assert result.company_name == "TechCorp"
        assert result.confidence == 0.95

    @patch('cufinder.client.requests.Session')
    def test_epp_service(self, mock_session):
        """Test EPP service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "person": {
                "full_name": "John Doe",
                "job_title": "Software Engineer"
            },
            "company": {
                "name": "TechCorp",
                "domain": "techcorp.com"
            },
            "confidence": 0.90
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.epp("https://linkedin.com/in/johndoe")

        assert result.person.full_name == "John Doe"
        assert result.person.job_title == "Software Engineer"
        assert result.company.name == "TechCorp"
        assert result.confidence == 0.90

    @patch('cufinder.client.requests.Session')
    def test_lbs_service(self, mock_session):
        """Test LBS service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "businesses": [
                {"name": "Coffee Shop", "address": "123 Main St"},
                {"name": "Restaurant", "address": "456 Oak Ave"}
            ],
            "total": 2,
            "page": 1
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.lbs(name="coffee", city="San Francisco")

        assert len(result.businesses) == 2
        assert result.total_results == 2
        assert result.businesses[0]["name"] == "Coffee Shop"

    @patch('cufinder.client.requests.Session')
    def test_dtc_service(self, mock_session):
        """Test DTC service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "company_name": "Example Corp",
            "company_website": "https://example.com",
            "confidence": 0.85
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.dtc("https://example.com")

        assert result.company_name == "Example Corp"
        assert result.company_website == "https://example.com"
        assert result.confidence == 0.85

    @patch('cufinder.client.requests.Session')
    def test_dte_service(self, mock_session):
        """Test DTE service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "emails": ["contact@example.com", "info@example.com"],
            "company_website": "https://example.com",
            "confidence": 0.80
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.dte("https://example.com")

        assert len(result.emails) == 2
        assert "contact@example.com" in result.emails
        assert result.confidence == 0.80

    @patch('cufinder.client.requests.Session')
    def test_ntp_service(self, mock_session):
        """Test NTP service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "phones": ["+1-555-123-4567", "+1-555-987-6543"],
            "company_name": "TechCorp",
            "confidence": 0.75
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.ntp("TechCorp")

        assert len(result.phones) == 2
        assert "+1-555-123-4567" in result.phones
        assert result.company_name == "TechCorp"

    @patch('cufinder.client.requests.Session')
    def test_rel_service(self, mock_session):
        """Test REL service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "person": {
                "full_name": "Jane Smith",
                "email": "jane@example.com"
            },
            "company": {
                "name": "Example Corp",
                "domain": "example.com"
            },
            "confidence": 0.88
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.rel("jane@example.com")

        assert result.person.full_name == "Jane Smith"
        assert result.person.email == "jane@example.com"
        assert result.company.name == "Example Corp"
        assert result.confidence == 0.88

    @patch('cufinder.client.requests.Session')
    def test_fcl_service(self, mock_session):
        """Test FCL service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "lookalikes": [
                {"name": "SimilarCorp", "similarity": 0.85},
                {"name": "LikeCorp", "similarity": 0.78}
            ],
            "query": "TechCorp",
            "total": 2
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.fcl("TechCorp")

        assert len(result.companies) == 2
        assert result.total == 2
        assert result.companies[0]["name"] == "SimilarCorp"

    @patch('cufinder.client.requests.Session')
    def test_elf_service(self, mock_session):
        """Test ELF service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "fundraising": {
                "total_raised": "$10M",
                "rounds": ["Series A", "Series B"]
            },
            "query": "TechCorp",
            "confidence": 0.82
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.elf("TechCorp")

        assert result.fundraising["total_raised"] == "$10M"
        assert len(result.fundraising["rounds"]) == 2
        assert result.confidence == 0.82

    @patch('cufinder.client.requests.Session')
    def test_car_service(self, mock_session):
        """Test CAR service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "revenue": "$50M - $100M",
            "query": "TechCorp",
            "confidence": 0.75
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.car("TechCorp")

        assert result.revenue == "$50M - $100M"
        assert result.query == "TechCorp"
        assert result.confidence == 0.75

    @patch('cufinder.client.requests.Session')
    def test_fcc_service(self, mock_session):
        """Test FCC service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "subsidiaries": [
                {"name": "SubCorp1", "type": "subsidiary"},
                {"name": "SubCorp2", "type": "subsidiary"}
            ],
            "query": "Alphabet Inc",
            "total": 2
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.fcc("Alphabet Inc")

        assert len(result.subsidiaries) == 2
        assert result.total == 2
        assert result.subsidiaries[0]["name"] == "SubCorp1"

    @patch('cufinder.client.requests.Session')
    def test_fts_service(self, mock_session):
        """Test FTS service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "tech_stack": ["Python", "React", "AWS", "Docker"],
            "query": "TechCorp",
            "confidence": 0.90
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.fts("TechCorp")

        assert len(result.tech_stack) == 4
        assert "Python" in result.tech_stack
        assert "React" in result.tech_stack
        assert result.confidence == 0.90

    @patch('cufinder.client.requests.Session')
    def test_fwe_service(self, mock_session):
        """Test FWE service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "email": "john.doe@example.com",
            "profile_url": "https://linkedin.com/in/johndoe",
            "confidence": 0.85
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.fwe("https://linkedin.com/in/johndoe")

        assert result.work_email == "john.doe@example.com"
        assert result.profile_url == "https://linkedin.com/in/johndoe"
        assert result.confidence == 0.85

    @patch('cufinder.client.requests.Session')
    def test_tep_service(self, mock_session):
        """Test TEP service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "person": {
                "full_name": "John Doe",
                "job_title": "Software Engineer",
                "company": "TechCorp"
            },
            "query": "John Doe",
            "confidence": 0.88
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.tep("John Doe", "TechCorp")

        assert result.person.full_name == "John Doe"
        assert result.person.job_title == "Software Engineer"
        assert result.person.company == "TechCorp"
        assert result.confidence == 0.88

    @patch('cufinder.client.requests.Session')
    def test_enc_service(self, mock_session):
        """Test ENC service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "company": {
                "name": "TechCorp Inc",
                "industry": "Technology",
                "size": "100-500"
            },
            "query": "TechCorp",
            "confidence": 0.92
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.enc("TechCorp")

        assert result.company.name == "TechCorp Inc"
        assert result.company.industry == "Technology"
        assert result.company.size == "100-500"
        assert result.confidence == 0.92

    @patch('cufinder.client.requests.Session')
    def test_cec_service(self, mock_session):
        """Test CEC service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "countries": ["United States", "Canada", "United Kingdom"],
            "query": "TechCorp",
            "total": 3
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.cec("TechCorp")

        assert len(result.countries) == 3
        assert "United States" in result.countries
        assert "Canada" in result.countries
        assert result.total == 3

    @patch('cufinder.client.requests.Session')
    def test_clo_service(self, mock_session):
        """Test CLO service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "locations": [
                {"city": "San Francisco", "country": "USA"},
                {"city": "New York", "country": "USA"}
            ],
            "query": "TechCorp",
            "total": 2
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.clo("TechCorp")

        assert len(result.locations) == 2
        assert result.locations[0]["city"] == "San Francisco"
        assert result.total == 2

    @patch('cufinder.client.requests.Session')
    def test_cse_service(self, mock_session):
        """Test CSE service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "companies": [
                {"name": "TechCorp", "industry": "Software"},
                {"name": "DataCorp", "industry": "Analytics"}
            ],
            "total": 2,
            "page": 1
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.cse(name="tech", industry="software")

        assert len(result.companies) == 2
        assert result.total_results == 2
        assert result.companies[0]["name"] == "TechCorp"

    @patch('cufinder.client.requests.Session')
    def test_pse_service(self, mock_session):
        """Test PSE service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "people": [
                {"name": "John Doe", "title": "Software Engineer"},
                {"name": "Jane Smith", "title": "Product Manager"}
            ],
            "total": 2,
            "page": 1
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.pse(full_name="engineer", company_name="TechCorp")

        assert len(result.people) == 2
        assert result.total_results == 2
        assert result.people[0]["name"] == "John Doe"

    @patch('cufinder.client.requests.Session')
    def test_lcuf_service(self, mock_session):
        """Test LCUF service method."""
        # Mock response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "linkedin_url": "https://linkedin.com/company/techcorp",
            "company_name": "TechCorp",
            "confidence": 0.95
        }
        mock_session.return_value.request.return_value = mock_response

        sdk = Cufinder(api_key="test-key")
        result = sdk.lcuf("TechCorp")

        assert result.linkedin_url == "https://linkedin.com/company/techcorp"
        assert result.company_name == "TechCorp"
        assert result.confidence == 0.95
