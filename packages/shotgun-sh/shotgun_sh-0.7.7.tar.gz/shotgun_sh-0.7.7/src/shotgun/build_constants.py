"""Build-time constants generated during packaging.

This file is auto-generated during the build process.
DO NOT EDIT MANUALLY.
"""

# PostHog configuration embedded at build time (empty strings if not provided)
POSTHOG_API_KEY = 'phc_KKnChzZUKeNqZDOTJ6soCBWNQSx3vjiULdwTR9H5Mcr'
POSTHOG_PROJECT_ID = '191396'

# Logfire configuration embedded at build time (only for dev builds)
LOGFIRE_ENABLED = ''
LOGFIRE_TOKEN = ''

# Build metadata
BUILD_TIME_ENV = "production" if POSTHOG_API_KEY else "development"
IS_DEV_BUILD = False
