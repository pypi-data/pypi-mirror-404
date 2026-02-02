# noqa-runner

AI-powered mobile test execution runner for iOS applications.

## Installation

```bash
pip install noqa-runner
```

## Quick Start

### CLI

```bash
# Run on physical device with local IPA build
python -m noqa_runner run \
  --noqa-api-token $NOQA_API_TOKEN \
  --case-input-json '[
    {
      "case_instructions": "Open app and login with valid credentials"
    }
  ]' \
  --device-id "00008110-001234567890001E" \
  --apple-developer-team-id TEAM123456 \
  --app-bundle-id com.example.app \
  --build-path /path/to/app.ipa

# Run on iOS Simulator with .app build
python -m noqa_runner run \
  --noqa-api-token $NOQA_API_TOKEN \
  --case-input-json '[
    {
      "case_instructions": "Open app and login with valid credentials"
    }
  ]' \
  --simulator-id "SIMULATOR-UDID" \
  --app-bundle-id com.example.app \
  --build-path /path/to/MyApp.app

# Run on device with TestFlight installation
python -m noqa_runner run \
  --noqa-api-token $NOQA_API_TOKEN \
  --case-input-json '[
    {
      "case_instructions": "Open app and verify features"
    }
  ]' \
  --device-id "00008110-001234567890001E" \
  --apple-developer-team-id TEAM123456 \
  --app-bundle-id com.example.app \
  --app-store-id 123456789

```

**Required Options:**

```
--noqa-api-token TEXT         noqa API authentication token [required]
--case-input-json TEXT        JSON with test cases: [{case_instructions, test_id?, case_name?}] [required]
--app-bundle-id TEXT          App bundle ID (auto-extracted from build if not provided) [recommended]
```

**Target Options (choose one):**

```
--device-id TEXT              Device UDID for physical device testing
--simulator-id TEXT           Simulator UDID for simulator testing

**Device-Only Options:**

```
--apple-developer-team-id TEXT Apple Developer Team ID for code signing [required for devices]
--app-store-id TEXT           App Store ID for TestFlight installation (device only)
```

**Installation Options (choose one):**

```
--build-path TEXT             Path to local IPA build file
--app-store-id TEXT           App Store ID for TestFlight installation
```

**Other Options:**

```
--app-context TEXT            Application context information [optional]
--agent-api-url TEXT          Agent API base URL [optional, default: https://agent.noqa.ai]
--log-level TEXT              Logging level [optional, default: INFO]
```

### Python API

```python
from noqa_runner import RunnerSession, RunnerTestInfo

# Create session
session = RunnerSession()

# Run on physical device with local IPA build
results = await session.run(
    noqa_api_token="your-token",
    tests=[
        RunnerTestInfo(
            case_instructions="Open app and verify home screen",
        )
    ],
    device_id="00008110-001234567890001E",
    apple_developer_team_id="TEAM123456",
    app_bundle_id="com.example.app",
    app_build_path="/path/to/app.ipa",
)

# Run on iOS Simulator with .app build
results = await session.run(
    noqa_api_token="your-token",
    tests=[
        RunnerTestInfo(
            case_instructions="Open app and verify home screen",
        )
    ],
    simulator_id="SIMULATOR-UDID",
    app_bundle_id="com.example.app",
    app_build_path="/path/to/MyApp.app",
)

# Run with TestFlight installation
results = session.run(
    noqa_api_token="your-token",
    tests=[
        RunnerTestInfo(
            case_instructions="Open app and verify features",
        )
    ],
    device_id="00008110-001234567890001E",
    apple_developer_team_id="TEAM123456",
    app_bundle_id="com.example.app",
    app_store_id="123456789",
)
```

## Test Results

The CLI returns test results as JSON with detailed information about each test execution:

```json
[
  {
    "case_instructions": "Complete onboarding, check that paywall has products",
    "status": "passed",
    "message": "Test completed",
    "test_conditions": [
      {
        "condition": "Onboarding process was completed successfully",
        "is_verified": true,
        "evidence": "User progressed through multiple onboarding screens, ending with 'Get started' button",
        "step_number": 4,
        "confidence": 100
      },
      ...
    ],
    "steps": [...]
  }
]
```

## Support

For issues and questions https://noqa.ai/
