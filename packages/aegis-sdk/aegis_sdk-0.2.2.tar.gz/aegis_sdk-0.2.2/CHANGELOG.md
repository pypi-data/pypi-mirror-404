# Changelog

All notable changes to the Aegis SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-28

### Added

#### Core Features
- **Pattern Detection**: Comprehensive PII detection for emails, phone numbers, SSNs, credit cards (with Luhn validation), API secrets, IBANs, and PHI keywords
- **Format-Preserving Masking**: Mask sensitive data while preserving format (e.g., `john@example.com` → `j***@example.com`)
- **Policy Engine**: Configurable decision logic with ALLOWED, ALLOWED_WITH_MASKING, and BLOCKED decisions
- **Multiple Destinations**: Support for AI_TOOL, VENDOR, and CUSTOMER destinations with different masking rules

#### Batch Processing
- **StreamingProcessor**: Process files of any size (200MB+) with constant memory usage (~30MB)
- **CSVStreamProcessor**: Specialized CSV processing with column-level detection and selective masking
- **Progress callbacks**: Real-time progress reporting during file processing
- **Early termination**: Optional `stop_on_block` to halt processing on blocked content

#### LLM Integrations
- **AegisLLMGateway**: Base gateway for masking prompts and chat messages
- **AegisOpenAI**: Drop-in replacement for OpenAI client with automatic PII masking
- **AegisAnthropic**: Anthropic/Claude integration wrapper
- **LangChain Integration**: Callback handler and chain wrapper for LangChain
- **Reversible Masking**: Optional mask map storage for unmasking LLM responses
- **StreamingGateway**: Support for streaming LLM responses

#### Enterprise Features
- **LicenseManager**: License validation with local caching (24hr TTL)
- **OfflineLicenseManager**: Air-gapped deployment support with offline license files
- **Grace Period**: 7-day offline grace period for temporary connectivity issues
- **MetricsReporter**: Async, non-blocking metrics reporting to Aegis Cloud
- **LocalMetricsCollector**: Local metrics storage for air-gapped environments

#### Audit & Compliance
- **AuditLog**: Comprehensive audit logging with hash chain verification
- **GDPRAuditLog**: GDPR-compliant audit log (metadata-only, no PII samples)
- **Log Rotation**: Automatic rotation by size or age with optional compression
- **Retention Policy**: Configurable log retention with automatic cleanup
- **Data Subject Reports**: Generate reports for GDPR data subject requests

#### CLI Tool
- `aegis scan`: Scan text or files for PII
- `aegis mask`: Mask PII in text or files
- `aegis process`: Full processing with decision logic
- `aegis process-file`: Streaming file processing
- `aegis check-license`: Verify license status

### Security
- No customer data ever sent to cloud (metrics are aggregated counts only)
- Hash chain verification for audit log integrity
- Local-only data processing in SDK mode
- Support for air-gapped deployments

### Documentation
- Comprehensive README with all features documented
- Example scripts for common use cases
- API reference documentation

## [Unreleased]

### Planned
- Additional LLM provider integrations (Google Vertex AI, AWS Bedrock)
- Custom pattern definitions via configuration
- Policy DSL for complex rules
- Prometheus metrics export
- SIEM integration for audit logs
