"""
Feature Flag System for SoulEyez Interactive Menu

This module provides a centralized feature flag system to control
the availability of features in the interactive interface.
"""

from enum import Enum
from typing import Dict, Optional


class FeatureStatus(Enum):
    """Status of a feature."""

    ENABLED = "enabled"  # Feature is fully implemented and available
    DISABLED = "disabled"  # Feature is hidden from users
    BETA = "beta"  # Feature is available but marked as beta
    DEVELOPMENT = "development"  # Feature is under development (hidden in production)
    PRO = "pro"  # Feature requires Pro tier


class Feature(Enum):
    """Available features in SoulEyez."""

    # Export Features
    JSON_EXPORT = "json_export"
    HOSTS_SERVICES_EXPORT = "hosts_services_export"

    # Import Features
    NMAP_XML_IMPORT = "nmap_xml_import"
    NESSUS_IMPORT = "nessus_import"

    # Analysis Features
    EVIDENCE_LINKING = "evidence_linking"
    CORRELATION_ENGINE = "correlation_engine"
    ATTACK_SURFACE = "attack_surface"
    EXPLOIT_SUGGESTIONS = "exploit_suggestions"

    # Dashboard Features
    TEAM_DASHBOARD = "team_dashboard"
    TIMELINE_VIEW = "timeline_view"

    # Reporting Features
    DELIVERABLES = "deliverables"
    EXPORT_VIEW = "export_view"

    # Advanced Features
    AUTO_CHAINING = "auto_chaining"
    AI_RECOMMENDATIONS = "ai_recommendations"


class FeatureFlags:
    """
    Feature flag manager for controlling feature availability.

    Usage:
        if FeatureFlags.is_enabled(Feature.JSON_EXPORT):
            show_json_export_option()
    """

    # Feature flag configuration
    _flags: Dict[Feature, FeatureStatus] = {
        # Export Features - Placeholder implementations
        Feature.JSON_EXPORT: FeatureStatus.DISABLED,
        Feature.HOSTS_SERVICES_EXPORT: FeatureStatus.DISABLED,
        # Import Features - Placeholder implementations
        Feature.NMAP_XML_IMPORT: FeatureStatus.DISABLED,
        Feature.NESSUS_IMPORT: FeatureStatus.DISABLED,
        # Analysis Features
        Feature.EVIDENCE_LINKING: FeatureStatus.ENABLED,  # FREE - basic feature
        Feature.CORRELATION_ENGINE: FeatureStatus.PRO,  # PRO - advanced analysis
        Feature.ATTACK_SURFACE: FeatureStatus.PRO,  # PRO - priority scoring
        Feature.EXPLOIT_SUGGESTIONS: FeatureStatus.PRO,  # PRO - CVE/MSF recommendations
        # Dashboard Features
        Feature.TEAM_DASHBOARD: FeatureStatus.PRO,  # PRO - collaboration
        Feature.TIMELINE_VIEW: FeatureStatus.ENABLED,  # FREE - basic timeline
        # Reporting Features
        Feature.DELIVERABLES: FeatureStatus.ENABLED,  # FREE - basic tracking
        Feature.EXPORT_VIEW: FeatureStatus.PRO,  # PRO - report export
        # Advanced Features
        Feature.AUTO_CHAINING: FeatureStatus.PRO,  # PRO - automation
        Feature.AI_RECOMMENDATIONS: FeatureStatus.PRO,  # PRO - AI features
    }

    @classmethod
    def is_enabled(cls, feature: Feature, user_tier: str = None) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature: The feature to check
            user_tier: User's tier ('FREE' or 'PRO'). If None, Pro features return False.

        Returns:
            True if the feature is enabled or in beta, False otherwise
        """
        status = cls._flags.get(feature, FeatureStatus.DISABLED)

        # Pro features require Pro tier
        if status == FeatureStatus.PRO:
            return user_tier == "PRO"

        return status in (FeatureStatus.ENABLED, FeatureStatus.BETA)

    @classmethod
    def is_beta(cls, feature: Feature) -> bool:
        """
        Check if a feature is in beta status.

        Args:
            feature: The feature to check

        Returns:
            True if the feature is in beta
        """
        return cls._flags.get(feature, FeatureStatus.DISABLED) == FeatureStatus.BETA

    @classmethod
    def get_status(cls, feature: Feature) -> FeatureStatus:
        """
        Get the status of a feature.

        Args:
            feature: The feature to check

        Returns:
            The feature's status
        """
        return cls._flags.get(feature, FeatureStatus.DISABLED)

    @classmethod
    def set_status(cls, feature: Feature, status: FeatureStatus) -> None:
        """
        Set the status of a feature (for testing/development).

        Args:
            feature: The feature to modify
            status: The new status
        """
        cls._flags[feature] = status

    @classmethod
    def get_beta_label(cls) -> str:
        """Get the beta indicator label."""
        return "🧪 BETA"

    @classmethod
    def should_show_in_menu(cls, feature: Feature) -> bool:
        """
        Check if a feature should be shown in menus.
        Pro features are shown but gated with a lock icon.

        Args:
            feature: The feature to check

        Returns:
            True if the feature should be visible in menus
        """
        status = cls._flags.get(feature, FeatureStatus.DISABLED)
        return status in (FeatureStatus.ENABLED, FeatureStatus.BETA, FeatureStatus.PRO)

    @classmethod
    def is_pro(cls, feature: Feature) -> bool:
        """Check if a feature requires Pro tier."""
        return cls._flags.get(feature, FeatureStatus.DISABLED) == FeatureStatus.PRO

    @classmethod
    def get_pro_label(cls) -> str:
        """Get the Pro indicator label."""
        return "🔒 PRO"
