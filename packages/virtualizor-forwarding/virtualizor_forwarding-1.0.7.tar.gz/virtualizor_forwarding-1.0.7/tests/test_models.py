"""
Unit tests for data models.
"""

import json
import pytest
from virtualizor_forwarding.models import (
    Protocol,
    VMStatus,
    HostProfile,
    Config,
    VMInfo,
    ForwardingRule,
    HAProxyConfig,
    APIResponse,
    ValidationResult,
    BatchResult,
)


class TestProtocol:
    """Tests for Protocol enum."""

    def test_protocol_values(self):
        """Test protocol enum values."""
        assert Protocol.HTTP.value == "HTTP"
        assert Protocol.HTTPS.value == "HTTPS"
        assert Protocol.TCP.value == "TCP"

    def test_from_string_uppercase(self):
        """Test creating protocol from uppercase string."""
        assert Protocol.from_string("HTTP") == Protocol.HTTP
        assert Protocol.from_string("HTTPS") == Protocol.HTTPS
        assert Protocol.from_string("TCP") == Protocol.TCP

    def test_from_string_lowercase(self):
        """Test creating protocol from lowercase string."""
        assert Protocol.from_string("http") == Protocol.HTTP
        assert Protocol.from_string("https") == Protocol.HTTPS
        assert Protocol.from_string("tcp") == Protocol.TCP

    def test_from_string_mixed_case(self):
        """Test creating protocol from mixed case string."""
        assert Protocol.from_string("Http") == Protocol.HTTP
        assert Protocol.from_string("HtTpS") == Protocol.HTTPS

    def test_from_string_invalid(self):
        """Test invalid protocol string raises ValueError."""
        with pytest.raises(ValueError):
            Protocol.from_string("INVALID")


class TestVMStatus:
    """Tests for VMStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert VMStatus.UP.value == "up"
        assert VMStatus.DOWN.value == "down"

    def test_from_int_up(self):
        """Test creating status from int 1."""
        assert VMStatus.from_int(1) == VMStatus.UP

    def test_from_int_down(self):
        """Test creating status from int 0."""
        assert VMStatus.from_int(0) == VMStatus.DOWN

    def test_from_int_other(self):
        """Test creating status from other int values."""
        assert VMStatus.from_int(-1) == VMStatus.DOWN
        assert VMStatus.from_int(2) == VMStatus.DOWN


class TestHostProfile:
    """Tests for HostProfile dataclass."""

    def test_create_encodes_password(self):
        """Test that create() encodes password in base64."""
        profile = HostProfile.create(
            name="test",
            api_url="https://example.com:4083/index.php",
            api_key="mykey",
            api_pass="mypassword",
        )
        assert profile.name == "test"
        assert profile.api_url == "https://example.com:4083/index.php"
        assert profile.api_key == "mykey"
        # Password should be base64 encoded
        assert profile.api_pass != "mypassword"

    def test_get_decoded_pass(self):
        """Test password decoding."""
        profile = HostProfile.create(
            name="test",
            api_url="https://example.com:4083/index.php",
            api_key="mykey",
            api_pass="mypassword",
        )
        assert profile.get_decoded_pass() == "mypassword"

    def test_get_decoded_pass_unencoded(self):
        """Test decoding when password is not encoded."""
        profile = HostProfile(
            name="test",
            api_url="https://example.com:4083/index.php",
            api_key="mykey",
            api_pass="plaintext",  # Not base64
        )
        # Should return as-is if decoding fails
        result = profile.get_decoded_pass()
        assert result == "plaintext"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        profile = HostProfile(
            name="test",
            api_url="https://example.com:4083/index.php",
            api_key="mykey",
            api_pass="encoded",
        )
        d = profile.to_dict()
        assert d["name"] == "test"
        assert d["api_url"] == "https://example.com:4083/index.php"
        assert d["api_key"] == "mykey"
        assert d["api_pass"] == "encoded"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "name": "test",
            "api_url": "https://example.com:4083/index.php",
            "api_key": "mykey",
            "api_pass": "encoded",
        }
        profile = HostProfile.from_dict(data)
        assert profile.name == "test"
        assert profile.api_url == "https://example.com:4083/index.php"


class TestConfig:
    """Tests for Config dataclass."""

    def test_empty_config(self):
        """Test empty config initialization."""
        config = Config()
        assert config.hosts == {}
        assert config.default_host is None
        assert config.version == "1.0"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        profile = HostProfile(
            name="prod",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="pass",
        )
        config = Config(hosts={"prod": profile}, default_host="prod")
        d = config.to_dict()
        assert "hosts" in d
        assert "prod" in d["hosts"]
        assert d["default_host"] == "prod"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "hosts": {
                "prod": {
                    "name": "prod",
                    "api_url": "https://example.com:4083/index.php",
                    "api_key": "key",
                    "api_pass": "pass",
                }
            },
            "default_host": "prod",
            "version": "1.0",
        }
        config = Config.from_dict(data)
        assert "prod" in config.hosts
        assert config.default_host == "prod"

    def test_to_json_and_from_json(self):
        """Test JSON serialization round-trip."""
        profile = HostProfile(
            name="test",
            api_url="https://example.com:4083/index.php",
            api_key="key",
            api_pass="pass",
        )
        config = Config(hosts={"test": profile}, default_host="test")
        json_str = config.to_json()
        restored = Config.from_json(json_str)
        assert "test" in restored.hosts
        assert restored.default_host == "test"


class TestVMInfo:
    """Tests for VMInfo dataclass."""

    def test_basic_creation(self):
        """Test basic VMInfo creation."""
        vm = VMInfo(vpsid="123", hostname="myvm", ipv4="10.0.0.1", status=VMStatus.UP)
        assert vm.vpsid == "123"
        assert vm.hostname == "myvm"
        assert vm.ipv4 == "10.0.0.1"
        assert vm.status == VMStatus.UP

    def test_get_short_ipv6_none(self):
        """Test short IPv6 with no IPv6."""
        vm = VMInfo(vpsid="123", hostname="myvm")
        assert vm.get_short_ipv6() == "-"

    def test_get_short_ipv6_dash(self):
        """Test short IPv6 with dash value."""
        vm = VMInfo(vpsid="123", hostname="myvm", ipv6="-")
        assert vm.get_short_ipv6() == "-"

    def test_get_short_ipv6_valid(self):
        """Test short IPv6 with valid address."""
        vm = VMInfo(
            vpsid="123", hostname="myvm", ipv6="2001:0db8:0000:0000:0000:0000:0000:0001"
        )
        result = vm.get_short_ipv6()
        assert result == "2001:db8::1"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        vm = VMInfo(vpsid="123", hostname="myvm", ipv4="10.0.0.1", status=VMStatus.UP)
        d = vm.to_dict()
        assert d["vpsid"] == "123"
        assert d["hostname"] == "myvm"
        assert d["status"] == "up"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {"vpsid": "123", "hostname": "myvm", "ipv4": "10.0.0.1", "status": "up"}
        vm = VMInfo.from_dict(data)
        assert vm.vpsid == "123"
        assert vm.status == VMStatus.UP

    def test_from_dict_int_status(self):
        """Test creation from dictionary with int status."""
        data = {"vpsid": "123", "hostname": "myvm", "status": 1}
        vm = VMInfo.from_dict(data)
        assert vm.status == VMStatus.UP

    def test_from_api_response(self):
        """Test creation from API response."""
        data = {
            "hostname": "myvm",
            "status": 1,
            "ips": {"1": "10.0.0.1", "2": "2001:db8::1"},
        }
        vm = VMInfo.from_api_response("123", data)
        assert vm.vpsid == "123"
        assert vm.hostname == "myvm"
        assert vm.ipv4 == "10.0.0.1"
        assert vm.ipv6 == "2001:db8::1"
        assert vm.status == VMStatus.UP


class TestForwardingRule:
    """Tests for ForwardingRule dataclass."""

    def test_basic_creation(self):
        """Test basic rule creation."""
        rule = ForwardingRule(
            protocol=Protocol.HTTP,
            src_hostname="example.com",
            src_port=80,
            dest_ip="10.0.0.1",
            dest_port=80,
        )
        assert rule.protocol == Protocol.HTTP
        assert rule.src_hostname == "example.com"
        assert rule.src_port == 80

    def test_to_dict(self):
        """Test conversion to dictionary."""
        rule = ForwardingRule(
            protocol=Protocol.HTTPS,
            src_hostname="secure.example.com",
            src_port=443,
            dest_ip="10.0.0.1",
            dest_port=443,
            id="123",
        )
        d = rule.to_dict()
        assert d["protocol"] == "HTTPS"
        assert d["src_hostname"] == "secure.example.com"
        assert d["id"] == "123"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "protocol": "TCP",
            "src_hostname": "1.2.3.4",
            "src_port": 2222,
            "dest_ip": "10.0.0.1",
            "dest_port": 22,
        }
        rule = ForwardingRule.from_dict(data)
        assert rule.protocol == Protocol.TCP
        assert rule.src_port == 2222
        assert rule.dest_port == 22

    def test_json_round_trip(self):
        """Test JSON serialization round-trip."""
        rule = ForwardingRule(
            protocol=Protocol.HTTP,
            src_hostname="example.com",
            src_port=80,
            dest_ip="10.0.0.1",
            dest_port=80,
        )
        json_str = rule.to_json()
        restored = ForwardingRule.from_json(json_str)
        assert restored.protocol == rule.protocol
        assert restored.src_hostname == rule.src_hostname


class TestHAProxyConfig:
    """Tests for HAProxyConfig dataclass."""

    def test_empty_config(self):
        """Test empty HAProxy config."""
        config = HAProxyConfig()
        assert config.get_allowed_ports_list() == []
        assert config.get_reserved_ports_list() == []
        assert config.get_first_src_ip() is None

    def test_parse_simple_ports(self):
        """Test parsing simple port list."""
        config = HAProxyConfig(allowed_ports="80,443,8080")
        ports = config.get_allowed_ports_list()
        assert 80 in ports
        assert 443 in ports
        assert 8080 in ports

    def test_parse_port_range(self):
        """Test parsing port range."""
        config = HAProxyConfig(allowed_ports="8000-8005")
        ports = config.get_allowed_ports_list()
        assert ports == [8000, 8001, 8002, 8003, 8004, 8005]

    def test_parse_mixed_ports(self):
        """Test parsing mixed ports and ranges."""
        config = HAProxyConfig(allowed_ports="80,443,8000-8002")
        ports = config.get_allowed_ports_list()
        assert 80 in ports
        assert 443 in ports
        assert 8000 in ports
        assert 8001 in ports
        assert 8002 in ports

    def test_get_first_src_ip(self):
        """Test getting first source IP."""
        config = HAProxyConfig(src_ips="1.2.3.4,5.6.7.8")
        assert config.get_first_src_ip() == "1.2.3.4"

    def test_from_api_response_empty(self):
        """Test creation from empty API response."""
        config = HAProxyConfig.from_api_response({})
        assert config.allowed_ports is None

    def test_from_api_response(self):
        """Test creation from API response."""
        data = {
            "server_haconfigs": {
                "1": {
                    "haproxy_allowedports": "80,443",
                    "haproxy_reservedports": "22",
                    "haproxy_src_ips": "1.2.3.4",
                }
            }
        }
        config = HAProxyConfig.from_api_response(data)
        assert config.allowed_ports == "80,443"
        assert config.reserved_ports == "22"
        assert config.src_ips == "1.2.3.4"


class TestAPIResponse:
    """Tests for APIResponse dataclass."""

    def test_success_response(self):
        """Test successful API response."""
        data = {"done": {"msg": "Success"}}
        response = APIResponse.from_response(data)
        assert response.success is True
        assert response.message == "Success"
        assert response.error is None

    def test_error_response(self):
        """Test error API response."""
        data = {"done": {}, "error": {"src_port": "Port already in use"}}
        response = APIResponse.from_response(data)
        assert response.success is False
        assert response.error is not None

    def test_get_error_message_dict(self):
        """Test extracting error message from dict."""
        response = APIResponse(success=False, error={"src_port": "Port already in use"})
        assert response.get_error_message() == "Port already in use"

    def test_get_error_message_string(self):
        """Test extracting error message from string."""
        response = APIResponse(success=False, error="Something went wrong")
        assert response.get_error_message() == "Something went wrong"

    def test_get_error_message_none(self):
        """Test error message when no error."""
        response = APIResponse(success=True)
        assert response.get_error_message() is None


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_success(self):
        """Test successful validation."""
        result = ValidationResult.success()
        assert result.valid is True
        assert result.message is None

    def test_failure(self):
        """Test failed validation."""
        result = ValidationResult.failure("Invalid port", ["Try port 8080"])
        assert result.valid is False
        assert result.message == "Invalid port"
        assert "Try port 8080" in result.suggestions


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_initial_state(self):
        """Test initial batch result state."""
        result = BatchResult(total=5, succeeded=0, failed=0)
        assert result.total == 5
        assert result.is_complete_success is True  # No failures yet

    def test_add_success(self):
        """Test adding success."""
        result = BatchResult(total=5, succeeded=0, failed=0)
        result.add_success()
        assert result.succeeded == 1

    def test_add_failure(self):
        """Test adding failure."""
        result = BatchResult(total=5, succeeded=0, failed=0)
        result.add_failure({"error": "Something failed"})
        assert result.failed == 1
        assert len(result.errors) == 1

    def test_is_complete_success(self):
        """Test complete success check."""
        result = BatchResult(total=5, succeeded=5, failed=0)
        assert result.is_complete_success is True

    def test_is_partial_success(self):
        """Test partial success check."""
        result = BatchResult(total=5, succeeded=3, failed=2)
        assert result.is_partial_success is True
        assert result.is_complete_success is False
