# Adapter SDK v1

## Purpose

Define one stable contract for every Inbound Hub source connector.

A source adapter answers only one question: how to interact with a particular external source or channel. Domain meaning remains outside the adapter.

## Required adapter identity

Every adapter declares:
- adapter_id
- adapter_type
- version
- capabilities
- config schema version

## Capabilities

Supported capability flags:
- receive
- read
- send
- write
- delete
- modify

Adapters must fail closed when a requested operation is not declared.

## Required lifecycle interface

Each adapter implements:
- configure(config)
- validate_config()
- start()
- stop()
- pause()
- resume()
- health()
- status()
- checkpoint()
- restore_checkpoint()
- receive()/poll() or webhook handler when receive is supported
- send() when send is supported

## Normalized output

Inbound data must be converted to InboundEvent v1.

Adapters must preserve source identity where available:
- external_message_id
- conversation/thread id
- sender/recipient identity
- source timestamp
- attachment metadata
- source-specific metadata in a namespaced field

Credentials and secrets must never enter InboundEvent.

## Reliability

Every adapter must define:
- dedupe key
- checkpoint semantics
- retry policy
- backoff
- transient vs permanent errors
- delivery/receive idempotency behavior

## Health and observability

Status values:
- RUNNING
- PAUSED
- DEGRADED
- ERROR
- STOPPED

Health includes:
- last_check_at
- last_success_at
- last_error_code
- checkpoint summary
- capability set
- config version

Do not expose secret values in status or logs.

## Error contract

Adapter errors use stable codes, not raw provider exceptions.

Minimum categories:
- CONFIG_INVALID
- AUTH_FAILED
- RATE_LIMITED
- SOURCE_UNAVAILABLE
- TRANSIENT_NETWORK
- PAYLOAD_INVALID
- CHECKPOINT_INVALID
- PERMISSION_DENIED

## Configuration

Each adapter owns a versioned config schema.
Secrets are referenced externally (environment, OS credential store, vault, etc.) and must not be committed.

## Registration

Adapters register with AdapterRegistry through metadata plus a factory.
The coordinator and runtime must not contain source-specific if/else branches.

## Testing requirements

Each adapter must provide contract tests for:
- config validation
- capabilities
- lifecycle
- health/status
- dedupe
- checkpoint/restart
- transient retry
- permanent failure
- secret redaction
- normalized InboundEvent output
