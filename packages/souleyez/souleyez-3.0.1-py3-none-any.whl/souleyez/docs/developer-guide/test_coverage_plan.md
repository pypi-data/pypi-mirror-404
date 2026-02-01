# SoulEyez Test Coverage Plan

**Created:** October 28, 2025
**Owner:** Robert (CTO)
**Target:** 70%+ code coverage before EPIC 2 completion
**Timeline:** Late November 2025

---

## 🎯 Testing Goals

### Coverage Targets

| Component | Priority | Target Coverage | Rationale |
|-----------|----------|-----------------|-----------|
| Credential Encryption | P0 | 95%+ | Security-critical |
| Engagement Management | P0 | 85%+ | Core functionality |
| Parsers (Nmap, Metasploit) | P0 | 80%+ | Data integrity critical |
| Database Operations | P1 | 75%+ | Data loss prevention |
| AI Integration (EPIC 2) | P1 | 70%+ | New feature validation |
| CLI Commands | P2 | 60%+ | User-facing, manual tested |
| Report Generation | P2 | 60%+ | Lower risk, visual output |
| Utilities/Helpers | P3 | 50%+ | Simple functions |

**Overall Target:** 70%+ across entire codebase

---

## 📋 Test Categories

### 1. Unit Tests
**Purpose:** Test individual functions/methods in isolation
**Tools:** pytest (Python), Jest (JavaScript), or appropriate framework
**Coverage:** 70%+ of all functions

### 2. Integration Tests
**Purpose:** Test component interactions
**Tools:** pytest with fixtures, docker-compose for dependencies
**Coverage:** All critical workflows

### 3. End-to-End Tests
**Purpose:** Test complete user scenarios
**Tools:** pytest with real data, CLI automation
**Coverage:** Top 10 user workflows

### 4. Security Tests
**Purpose:** Validate security controls
**Tools:** Custom security test suite
**Coverage:** All security-sensitive code paths

### 5. Performance Tests
**Purpose:** Benchmark and regression testing
**Tools:** pytest-benchmark, custom profiling
**Coverage:** Critical performance paths

---

## 🧪 Detailed Test Plan by Component

### Component 1: Credential Encryption (P0 - 95% Target)

#### Test File: `tests/test_credential_encryption.py`

**Unit Tests:**
```python
class TestCredentialEncryption:
    """Test credential encryption/decryption functionality"""

    def test_encrypt_credential_basic(self):
        """Test encrypting a simple credential"""
        # Given a plaintext credential
        # When encrypted with master password
        # Then should return encrypted ciphertext

    def test_decrypt_credential_basic(self):
        """Test decrypting an encrypted credential"""
        # Given encrypted credential
        # When decrypted with correct master password
        # Then should return original plaintext

    def test_decrypt_with_wrong_password(self):
        """Test decryption fails with incorrect password"""
        # Given encrypted credential
        # When decrypted with wrong password
        # Then should raise AuthenticationError

    def test_encrypt_empty_credential(self):
        """Test encrypting empty/null credentials"""
        # Edge case: empty password

    def test_encrypt_unicode_credential(self):
        """Test encrypting unicode characters"""
        # Test: passwords with emojis, Chinese chars, etc.

    def test_encrypt_long_credential(self):
        """Test encrypting very long credentials (10KB+)"""
        # Edge case: large passwords/keys

    def test_key_derivation_function(self):
        """Test KDF produces consistent keys"""
        # Verify same password produces same encryption key

    def test_key_derivation_with_salt(self):
        """Test KDF uses unique salt per credential"""
        # Verify different salts produce different ciphertexts

    def test_aes_256_mode(self):
        """Test AES-256 in correct mode (GCM/CBC)"""
        # Verify encryption mode and parameters

    def test_credential_metadata_not_leaked(self):
        """Test ciphertext doesn't leak metadata"""
        # Verify length, format doesn't reveal info
```

**Integration Tests:**
```python
def test_credential_storage_retrieval(database_session):
    """Test storing and retrieving encrypted credentials"""
    # Full workflow: encrypt → store → retrieve → decrypt

def test_master_password_change(database_session):
    """Test re-encrypting all credentials with new password"""
    # Critical: changing master password

def test_credential_backup_restore(database_session):
    """Test credentials survive backup/restore cycle"""
    # Data integrity across operations
```

**Security Tests:**
```python
def test_timing_attack_resistance():
    """Test constant-time comparison for password verification"""

def test_no_plaintext_in_memory_dumps():
    """Test credentials aren't left in memory"""

def test_encryption_key_not_logged():
    """Verify encryption keys never appear in logs"""
```

---

### Component 2: Engagement Management (P0 - 85% Target)

#### Test File: `tests/test_engagement_management.py`

**Unit Tests:**
```python
class TestEngagementCRUD:
    """Test engagement create, read, update, delete operations"""

    def test_create_engagement(self):
        """Test creating a new engagement"""

    def test_create_engagement_with_invalid_data(self):
        """Test validation on engagement creation"""

    def test_read_engagement_by_id(self):
        """Test retrieving engagement by ID"""

    def test_update_engagement(self):
        """Test updating engagement details"""

    def test_delete_engagement(self):
        """Test deleting an engagement"""

    def test_delete_engagement_cascades_to_hosts(self):
        """Test deleting engagement removes associated data"""

    def test_list_all_engagements(self):
        """Test listing all engagements"""

    def test_filter_engagements_by_date(self):
        """Test filtering engagements by date range"""

    def test_search_engagements_by_name(self):
        """Test searching engagements by name"""

class TestHostManagement:
    """Test host operations within engagements"""

    def test_add_host_to_engagement(self):
        """Test adding a host to an engagement"""

    def test_add_duplicate_host(self):
        """Test handling duplicate host IPs"""

    def test_update_host_information(self):
        """Test updating host details"""

    def test_remove_host_from_engagement(self):
        """Test removing a host"""

    def test_host_with_multiple_services(self):
        """Test host with multiple services"""

class TestServiceManagement:
    """Test service operations"""

    def test_add_service_to_host(self):
        """Test adding a service to a host"""

    def test_update_service_details(self):
        """Test updating service information"""

    def test_service_with_credentials(self):
        """Test linking credentials to services"""

class TestCredentialManagement:
    """Test credential operations"""

    def test_add_credential_to_engagement(self):
        """Test adding credentials"""

    def test_credential_validation(self):
        """Test credential format validation"""

    def test_list_credentials_by_type(self):
        """Test filtering credentials (SSH, RDP, etc.)"""
```

**Integration Tests:**
```python
def test_complete_engagement_workflow(database_session):
    """Test full engagement lifecycle"""
    # Create engagement → add hosts → add services → add creds → delete

def test_engagement_with_large_dataset(database_session):
    """Test engagement with 1000+ hosts"""
    # Performance and scalability test

def test_concurrent_engagement_access(database_session):
    """Test multiple operations on same engagement"""
    # Race condition testing
```

---

### Component 3: Parsers (P0 - 80% Target)

#### Test File: `tests/test_parsers.py`

**Test Data:** Create `tests/fixtures/` with sample outputs:
- `nmap_simple.xml` - Simple Nmap scan
- `nmap_large.xml` - Large scan (100+ hosts)
- `nmap_malformed.xml` - Malformed XML
- `metasploit_session.json` - Metasploit session data
- `metasploit_empty.json` - Empty results

**Unit Tests:**
```python
class TestNmapParser:
    """Test Nmap XML parser"""

    def test_parse_simple_nmap_scan(self):
        """Test parsing basic Nmap output"""
        # Load nmap_simple.xml and verify parsing

    def test_parse_host_discovery(self):
        """Test extracting host information"""

    def test_parse_service_detection(self):
        """Test extracting service details"""

    def test_parse_os_detection(self):
        """Test extracting OS information"""

    def test_parse_script_output(self):
        """Test parsing NSE script results"""

    def test_parse_malformed_xml(self):
        """Test handling malformed Nmap XML"""
        # Should raise ParseError

    def test_parse_empty_scan(self):
        """Test parsing scan with no results"""

    def test_parse_large_scan(self):
        """Test parsing scan with 1000+ hosts"""
        # Performance test

class TestMetasploitParser:
    """Test Metasploit parser"""

    def test_parse_session_data(self):
        """Test parsing Metasploit session info"""

    def test_parse_credential_dumps(self):
        """Test extracting credentials from sessions"""

    def test_parse_route_information(self):
        """Test extracting network routes"""

    def test_parse_empty_results(self):
        """Test handling empty Metasploit data"""

class TestParserBase:
    """Test parser base class functionality"""

    def test_parser_registration(self):
        """Test parser plugin system"""

    def test_parser_format_detection(self):
        """Test automatic format detection"""

    def test_parser_error_handling(self):
        """Test parser error propagation"""
```

**Integration Tests:**
```python
def test_nmap_import_to_engagement(database_session):
    """Test full Nmap import workflow"""
    # Parse → create hosts → create services → store in DB

def test_metasploit_import_with_credentials(database_session):
    """Test Metasploit import with credential extraction"""
    # Parse → extract creds → encrypt → store

def test_multiple_imports_same_engagement(database_session):
    """Test importing multiple scans to same engagement"""
    # Test deduplication and merging
```

**Security Tests:**
```python
def test_xml_entity_expansion_prevention():
    """Test parser prevents XXE attacks"""
    # Try malicious XML with entity expansion

def test_path_traversal_in_file_paths():
    """Test parser sanitizes file paths"""

def test_command_injection_in_script_output():
    """Test parser sanitizes Nmap script output"""
```

---

### Component 4: AI Integration - EPIC 2 (P1 - 70% Target)

#### Test File: `tests/test_ai_integration.py`

**Unit Tests:**
```python
class TestOllamaIntegration:
    """Test Ollama/LLM integration"""

    def test_ollama_connection(self):
        """Test connecting to Ollama service"""

    def test_ollama_model_loading(self):
        """Test loading Llama 3.1 model"""

    def test_ollama_inference_basic(self):
        """Test basic LLM inference"""

    def test_ollama_timeout_handling(self):
        """Test handling inference timeouts"""

    def test_ollama_connection_failure(self):
        """Test graceful handling of Ollama unavailability"""

    def test_ollama_context_window_management(self):
        """Test handling large context inputs"""

class TestAttackPathSuggestions:
    """Test AI attack-path recommendation logic"""

    def test_suggest_next_step_basic(self):
        """Test generating single-step recommendation"""

    def test_suggest_multi_step_attack_path(self):
        """Test generating multi-step attack chain"""

    def test_attack_path_with_credentials(self):
        """Test recommendations using available credentials"""

    def test_attack_path_scoring(self):
        """Test attack path risk scoring"""

    def test_attack_path_ranking(self):
        """Test ranking multiple suggestions"""

    def test_attack_path_with_no_data(self):
        """Test handling engagement with no scan data"""

class TestAIContextBuilding:
    """Test context preparation for LLM"""

    def test_build_context_from_engagement(self):
        """Test creating context from engagement data"""

    def test_context_size_limits(self):
        """Test context truncation for large engagements"""

    def test_context_includes_credentials(self):
        """Test credentials are included in context"""

    def test_context_includes_vulnerabilities(self):
        """Test known vulnerabilities included in context"""
```

**Integration Tests:**
```python
@pytest.mark.integration
@pytest.mark.requires_ollama
def test_end_to_end_ai_recommendation(database_session, ollama_instance):
    """Test complete AI recommendation workflow"""
    # Create engagement → import scan → generate AI suggestion

def test_ai_recommendation_caching(database_session):
    """Test caching of AI recommendations"""
    # Verify same context doesn't regenerate

def test_ai_with_multiple_engagements(database_session):
    """Test AI context isolation between engagements"""
```

**Performance Tests:**
```python
def test_ollama_inference_performance():
    """Benchmark Ollama inference time"""
    # Target: <5 seconds for recommendation

def test_context_building_performance():
    """Benchmark context preparation time"""
    # Target: <1 second for 1000 host engagement
```

---

### Component 5: License Validation - EPIC 2 (P1 - 75% Target)

#### Test File: `tests/test_license_validation.py`

**Unit Tests:**
```python
class TestLicenseGeneration:
    """Test license key generation"""

    def test_generate_license_key(self):
        """Test generating a valid license key"""

    def test_license_key_format(self):
        """Test license key follows expected format"""

    def test_license_key_uniqueness(self):
        """Test license keys are unique"""

class TestLicenseValidation:
    """Test license validation logic"""

    def test_validate_valid_license(self):
        """Test validating a valid license"""

    def test_validate_invalid_license(self):
        """Test rejecting invalid license"""

    def test_validate_expired_license(self):
        """Test rejecting expired license"""

    def test_validate_license_signature(self):
        """Test license signature verification"""

class TestFeatureGating:
    """Test Pro vs Free feature access"""

    def test_free_tier_feature_access(self):
        """Test free tier can access core features"""

    def test_free_tier_pro_feature_blocked(self):
        """Test free tier cannot access Pro features"""

    def test_pro_tier_feature_access(self):
        """Test Pro tier can access all features"""

    def test_expired_pro_downgrade(self):
        """Test expired Pro license reverts to free"""
```

**Integration Tests:**
```python
def test_stripe_webhook_handling():
    """Test handling Stripe subscription events"""
    # Mock Stripe webhooks

def test_license_upgrade_workflow():
    """Test upgrading from free to Pro"""

def test_license_downgrade_workflow():
    """Test downgrading from Pro to free"""
```

---

### Component 6: CLI Commands (P2 - 60% Target)

#### Test File: `tests/test_cli.py`

**Integration Tests:**
```python
class TestCLICommands:
    """Test CLI command execution"""

    def test_cli_help_command(self):
        """Test 'souleyez --help' command"""

    def test_cli_version_command(self):
        """Test 'souleyez --version' command"""

    def test_cli_engagement_create(self):
        """Test creating engagement via CLI"""

    def test_cli_import_nmap(self):
        """Test importing Nmap scan via CLI"""

    def test_cli_ai_suggest(self):
        """Test AI suggestion via CLI"""

    def test_cli_report_generate(self):
        """Test report generation via CLI"""

    def test_cli_invalid_command(self):
        """Test handling invalid CLI commands"""

    def test_cli_error_messages(self):
        """Test CLI error message formatting"""
```

---

## 🛠️ Testing Infrastructure

### Test Framework Setup

**Python Project (pytest):**
```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-mock pytest-benchmark

# Run all tests
pytest

# Run with coverage report
pytest --cov=souleyez --cov-report=html

# Run specific test category
pytest tests/test_credential_encryption.py

# Run performance tests
pytest --benchmark-only
```

**Project Structure:**
```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── fixtures/                       # Test data
│   ├── nmap_simple.xml
│   ├── nmap_large.xml
│   ├── metasploit_session.json
│   └── sample_engagement.json
├── test_credential_encryption.py
├── test_engagement_management.py
├── test_parsers.py
├── test_ai_integration.py
├── test_license_validation.py
├── test_cli.py
└── test_database.py
```

### Shared Fixtures (conftest.py)

```python
import pytest
from souleyez.database import Database
from souleyez.models import Engagement, Host, Service

@pytest.fixture
def database_session():
    """Provide a test database session"""
    db = Database(":memory:")  # In-memory SQLite for tests
    yield db.session
    db.session.rollback()
    db.close()

@pytest.fixture
def sample_engagement(database_session):
    """Create a sample engagement for testing"""
    engagement = Engagement(
        name="Test Engagement",
        client="Test Client",
        start_date="2025-10-01"
    )
    database_session.add(engagement)
    database_session.commit()
    return engagement

@pytest.fixture
def sample_host(database_session, sample_engagement):
    """Create a sample host for testing"""
    host = Host(
        engagement_id=sample_engagement.id,
        ip_address="192.168.1.10",
        hostname="testhost"
    )
    database_session.add(host)
    database_session.commit()
    return host

@pytest.fixture
def ollama_instance():
    """Mock or real Ollama instance for testing"""
    # Can be mocked for unit tests, real for integration tests
    pass

@pytest.fixture
def master_password():
    """Standard test master password"""
    return "TestMasterPassword123!"
```

---

## 📊 Test Execution Plan

### Phase 1: Critical Security Tests (Week 1 - Late Nov)
**Priority:** P0
**Target:** 95% coverage on credential encryption

**Tasks:**
- [ ] Write all credential encryption tests
- [ ] Write security-specific tests (timing attacks, XXE, etc.)
- [ ] Run security test suite
- [ ] Fix any security issues found
- [ ] Achieve 95%+ coverage on encryption module

**Deliverable:** All P0 security tests passing

---

### Phase 2: Core Functionality Tests (Week 1-2 - Late Nov)
**Priority:** P0
**Target:** 85% coverage on engagement management, 80% on parsers

**Tasks:**
- [ ] Write engagement management tests
- [ ] Write parser tests (Nmap, Metasploit)
- [ ] Create test fixtures (sample scan files)
- [ ] Run full test suite
- [ ] Fix bugs discovered
- [ ] Achieve target coverage

**Deliverable:** Core functionality fully tested

---

### Phase 3: EPIC 2 Feature Tests (Week 2-3 - Early Dec)
**Priority:** P1
**Target:** 70% coverage on AI integration and licensing

**Tasks:**
- [ ] Write Ollama integration tests
- [ ] Write attack-path suggestion tests
- [ ] Write license validation tests
- [ ] Write Stripe integration tests
- [ ] Mock external services appropriately
- [ ] Achieve target coverage

**Deliverable:** EPIC 2 features have comprehensive tests

---

### Phase 4: Integration & E2E Tests (Week 3-4 - Early Dec)
**Priority:** P1-P2
**Target:** All critical workflows covered

**Tasks:**
- [ ] Write end-to-end workflow tests
- [ ] Write CLI integration tests
- [ ] Write performance benchmarks
- [ ] Run full integration suite
- [ ] Document test coverage gaps

**Deliverable:** Complete integration test suite

---

### Phase 5: Continuous Testing (Ongoing)
**Priority:** P2-P3
**Target:** Maintain 70%+ coverage

**Tasks:**
- [ ] Set up CI/CD test automation
- [ ] Add test coverage reporting
- [ ] Enforce coverage minimums in CI
- [ ] Run tests on every commit
- [ ] Monthly test review and cleanup

**Deliverable:** Automated testing pipeline

---

## ✅ Test Coverage Verification

### Coverage Report Command
```bash
pytest --cov=souleyez --cov-report=html --cov-report=term
```

### Minimum Coverage Gates (CI/CD)
```yaml
# .github/workflows/test.yml
coverage:
  status:
    project:
      default:
        target: 70%
        threshold: 5%
    patch:
      default:
        target: 80%
```

### Coverage Exemptions
Exclude from coverage requirements:
- CLI argument parsing boilerplate
- Logging statements
- Exception message strings
- Type annotations
- Abstract base classes with no logic

---

## 🚨 Testing Best Practices

### 1. Test Naming Convention
```python
# Good
def test_encrypt_credential_with_strong_password():
    pass

# Bad
def test1():
    pass
```

### 2. Test Independence
- Each test should be runnable independently
- Tests should not depend on execution order
- Use fixtures for setup/teardown

### 3. Test Data Management
- Use fixtures for reusable test data
- Store complex test data in `tests/fixtures/`
- Never use production data in tests

### 4. Mocking External Services
- Mock Ollama for unit tests
- Mock Stripe API for payment tests
- Use real services only for integration tests

### 5. Performance Testing
- Benchmark critical operations
- Set performance thresholds in tests
- Fail tests if performance degrades

### 6. Security Testing
- Test for common vulnerabilities (SQLi, XSS, XXE)
- Test authentication and authorization
- Test encryption and key management

---

## 📋 Test Tracking Checklist

### Week 1 (Late November)
- [ ] Set up test infrastructure (pytest, fixtures)
- [ ] Write credential encryption tests (95% target)
- [ ] Write engagement management tests (50% complete)
- [ ] Coverage: ~40%

### Week 2 (Late November)
- [ ] Complete engagement management tests (85% target)
- [ ] Write parser tests (80% target)
- [ ] Create test fixtures for parsers
- [ ] Coverage: ~60%

### Week 3 (Early December)
- [ ] Write AI integration tests (70% target)
- [ ] Write license validation tests (75% target)
- [ ] Write CLI tests (60% target)
- [ ] Coverage: ~70%

### Week 4 (Early December)
- [ ] Write integration tests
- [ ] Write performance tests
- [ ] Set up CI/CD testing
- [ ] Coverage: 70%+ ✅

---

## 🎯 Success Criteria

**Tests are considered complete when:**
- [ ] Overall coverage ≥70%
- [ ] Security-critical code ≥95% coverage
- [ ] All P0 and P1 components tested
- [ ] CI/CD pipeline runs tests automatically
- [ ] Test suite runs in <5 minutes
- [ ] Zero flaky tests
- [ ] All tests documented with clear descriptions
- [ ] Test fixtures committed to repository

---

**Created:** October 28, 2025
**Owner:** Robert (CTO)
**Timeline:** Late November - Early December 2025
**Review:** December 15, 2025

