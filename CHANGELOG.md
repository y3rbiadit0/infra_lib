# Changelog

All notable changes to this project will be documented in this file.

## 0.1.9 [Feature] Environment context extra env vars hook - 2026-05-12
- Added `EnvironmentContext.get_extra_env_vars()` as a public hook for subclasses to provide additional container environment variables without overriding private build logic
- Updated container environment variable loading to apply precedence as dotenv files, `TARGET_ENV`, context extra env vars, then explicit `load(extra_vars)` overrides
- Documented the environment variable precedence directly in `EnvironmentContext.load` to clarify hook intent and avoid ambiguity around secrets and generated env files
- Added focused tests for default hook behavior, subclass-provided extra env vars, dotenv override precedence, and explicit load override precedence

## 0.1.1 [Fix] Regression tests and version bumping - 2025-10-31
- Added regression tests to cover existing behavior and prevent repeat failures
- Updated the version bump script to support different version increments
- Fixed several bugs in the codebase
- Planned follow-up cleanup for test code simplicity and readability

## 0.0.12 [Refactor] Operation decorator environment context runner - 2025-10-28
- Refactored operations to use the `@infra_operation` decorator annotation
- Refactored environment configuration around `EnvironmentContext` for operation execution
- Updated `runner_cli` to work with the operation decorator and environment context changes
- Planned follow-up improvements for the test suite and template runner updates

## 0.0.6 [Feature] Lambda code updates infra tasks and deploy CLI - 2025-10-23
- Added support for `update_function_code` in `lambda_util`
- Added support for `infra_task`
- Added a deploy CLI command to run tasks through the `infra_lib` CLI tool
- Added minor tests for the new functionality

## 0.0.3 [Feature] Flexible Docker Compose settings - 2025-10-13
- Added `ComposeSettings` to handle Docker Compose settings flexibly
- Added seamless profile handling through `ComposeSettings`
- Added `compose_settings()` to `BaseInfraBuilder`

## 0.0.2 [Feature] Custom lambda builder and LocalStack URLs - 2025-10-13
- Added `custom_lambda_builder` to `AWSLambdaParameters` for flexible Lambda zip building
- Refactored URLs to use modern LocalStack URL formats
- Added `scripts/bump_version` to automate version bumping for PowerShell

## 0.0.1 [Feature] Initial infra-lib release - 2025-09-30
- Added the first naive version of infra-lib to simplify running and setting up local infrastructure for a project
