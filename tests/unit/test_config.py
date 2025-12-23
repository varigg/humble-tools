"""Unit tests for configuration module.

Test Coverage:
- Default configuration values from constants
- Custom configuration values
- Validation for max_concurrent_downloads (must be >= 1)
- Validation for notification_duration (must be >= 1)
- Validation for item_removal_delay (must be >= 0)
- Output directory type handling (string to Path conversion)
- Partial configuration with defaults

Performance: All tests are fast (< 0.01s each)
Dependencies: Uses AppConfig dataclass and constants module
"""

from pathlib import Path

import pytest

from humble_tools.sync.config import AppConfig
from humble_tools.sync.constants import (
    DEFAULT_MAX_CONCURRENT_DOWNLOADS,
    DEFAULT_OUTPUT_DIR,
    ITEM_REMOVAL_DELAY_SECONDS,
    NOTIFICATION_DURATION_SECONDS,
)


class TestAppConfig:
    """Test AppConfig dataclass."""

    def test_default_configuration(self):
        """Test AppConfig creates with correct defaults."""
        config = AppConfig()

        assert config.max_concurrent_downloads == DEFAULT_MAX_CONCURRENT_DOWNLOADS
        assert config.notification_duration == NOTIFICATION_DURATION_SECONDS
        assert config.item_removal_delay == ITEM_REMOVAL_DELAY_SECONDS
        assert config.output_dir == DEFAULT_OUTPUT_DIR

    def test_custom_configuration(self):
        """Test AppConfig accepts custom values."""
        custom_dir = Path("/tmp/custom")
        config = AppConfig(
            max_concurrent_downloads=5,
            notification_duration=3,
            item_removal_delay=15,
            output_dir=custom_dir,
        )

        assert config.max_concurrent_downloads == 5
        assert config.notification_duration == 3
        assert config.item_removal_delay == 15
        assert config.output_dir == custom_dir

    @pytest.mark.parametrize(
        "value,expected_error",
        [
            (0, "max_concurrent_downloads must be at least 1"),
            (-1, "max_concurrent_downloads must be at least 1"),
        ],
    )
    def test_validation_max_concurrent_downloads(self, value, expected_error):
        """Test max_concurrent_downloads validation."""
        with pytest.raises(ValueError, match=expected_error):
            AppConfig(max_concurrent_downloads=value)

    @pytest.mark.parametrize(
        "value,expected_error",
        [
            (0, "notification_duration must be at least 1"),
            (-1, "notification_duration must be at least 1"),
        ],
    )
    def test_validation_notification_duration(self, value, expected_error):
        """Test notification_duration validation."""
        with pytest.raises(ValueError, match=expected_error):
            AppConfig(notification_duration=value)

    def test_validation_item_removal_delay_negative(self):
        """Test validation rejects negative item_removal_delay."""
        with pytest.raises(ValueError, match="item_removal_delay cannot be negative"):
            AppConfig(item_removal_delay=-1)

    def test_validation_item_removal_delay_zero_allowed(self):
        """Test validation allows zero item_removal_delay."""
        config = AppConfig(item_removal_delay=0)
        assert config.item_removal_delay == 0

    @pytest.mark.parametrize(
        "input_value,expected_type",
        [
            ("/tmp/test", Path),  # String conversion
            (Path("/tmp/test"), Path),  # Path preserved
        ],
    )
    def test_output_dir_type_handling(self, input_value, expected_type):
        """Test output_dir handles both string and Path."""
        config = AppConfig(output_dir=input_value)
        assert isinstance(config.output_dir, expected_type)
        assert config.output_dir == Path("/tmp/test")

    def test_partial_configuration(self):
        """Test AppConfig allows partial configuration."""
        config = AppConfig(max_concurrent_downloads=10)

        assert config.max_concurrent_downloads == 10
        assert config.notification_duration == NOTIFICATION_DURATION_SECONDS
        assert config.item_removal_delay == ITEM_REMOVAL_DELAY_SECONDS
        assert config.output_dir == DEFAULT_OUTPUT_DIR
