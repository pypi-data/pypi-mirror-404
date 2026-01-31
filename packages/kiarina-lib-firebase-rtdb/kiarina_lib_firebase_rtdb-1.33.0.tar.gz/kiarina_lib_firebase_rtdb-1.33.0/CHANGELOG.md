# Changelog

All notable changes to kiarina-lib-firebase-rtdb will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.33.0] - 2026-01-31

### Added
- Initial release with Firebase Realtime Database REST API integration
- `get_data()` function for retrieving data from Firebase RTDB
- `watch_data()` function for real-time data watching with Server-Sent Events
- `DataChangeEvent` schema for representing data change events
- `RTDBStreamCancelledError` exception for stream cancellation handling
- Automatic ID token refresh via `TokenManager` integration
- Network error handling with exponential backoff retry
- Configurable retry settings via `RTDBSettings`
- Comprehensive test suite with Firebase Admin SDK integration
- Example script for testing watch functionality
