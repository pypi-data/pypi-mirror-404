"""
Varity URL Service

Generates custom *.varity.app domains and short links for deployments.
Replaces raw IPFS/Akash URLs with user-friendly branded domains.
"""

import hashlib
import re
from typing import Optional, Tuple


class VarityURLService:
    """
    Generate custom Varity domains and short links for deployments.

    Provides user-friendly URLs:
    - my-app-abc123.varity.app (custom subdomain)
    - varity.app/a/xyz789 (short link)

    Instead of:
    - ipfs.io/ipfs/QmHash... (IPFS)
    - provider.akash.network/... (Akash)
    """

    BASE_DOMAIN = "varity.app"
    SHORT_LINK_PREFIX = "a"  # varity.app/a/...

    def __init__(self):
        """Initialize URL service"""
        pass

    def generate_subdomain(
        self,
        deployment_id: str,
        app_name: Optional[str] = None,
        project_type: Optional[str] = None
    ) -> str:
        """
        Generate custom subdomain for deployment.

        Format: {app-name}-{hash}.varity.app

        Args:
            deployment_id: Unique deployment ID
            app_name: Application name (optional, from package.json)
            project_type: Project type (optional, e.g., "nextjs", "react")

        Returns:
            Full subdomain URL (e.g., "my-app-abc123.varity.app")

        Examples:
            >>> service = VarityURLService()
            >>> service.generate_subdomain("deploy-123", "my-dashboard")
            'my-dashboard-abc123.varity.app'

            >>> service.generate_subdomain("deploy-456")
            'app-def456.varity.app'
        """
        # Sanitize app name
        if app_name:
            # Convert to lowercase, replace non-alphanumeric with hyphens
            sanitized_name = re.sub(r'[^a-z0-9]+', '-', app_name.lower())
            # Remove leading/trailing hyphens
            sanitized_name = sanitized_name.strip('-')
            # Limit length
            sanitized_name = sanitized_name[:30]
        else:
            sanitized_name = "app"

        # Generate deterministic hash from deployment_id
        hash_obj = hashlib.sha256(deployment_id.encode())
        hash_hex = hash_obj.hexdigest()[:6]  # First 6 chars

        # Build subdomain
        subdomain = f"{sanitized_name}-{hash_hex}"

        return f"{subdomain}.{self.BASE_DOMAIN}"

    def generate_short_link(self, deployment_id: str) -> str:
        """
        Generate short link for deployment.

        Format: varity.app/a/{hash}

        Args:
            deployment_id: Unique deployment ID

        Returns:
            Short link URL (e.g., "varity.app/a/xyz789")

        Examples:
            >>> service = VarityURLService()
            >>> service.generate_short_link("deploy-123")
            'varity.app/a/abc123'
        """
        # Generate deterministic hash from deployment_id
        hash_obj = hashlib.sha256(deployment_id.encode())
        hash_hex = hash_obj.hexdigest()[:6]  # First 6 chars

        return f"{self.BASE_DOMAIN}/{self.SHORT_LINK_PREFIX}/{hash_hex}"

    def generate_urls(
        self,
        deployment_id: str,
        app_name: Optional[str] = None,
        project_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate both subdomain and short link.

        Args:
            deployment_id: Unique deployment ID
            app_name: Application name (optional)
            project_type: Project type (optional)

        Returns:
            Tuple of (subdomain_url, short_link)

        Examples:
            >>> service = VarityURLService()
            >>> subdomain, short = service.generate_urls("deploy-123", "my-app")
            >>> print(subdomain)
            'my-app-abc123.varity.app'
            >>> print(short)
            'varity.app/a/abc123'
        """
        subdomain = self.generate_subdomain(deployment_id, app_name, project_type)
        short_link = self.generate_short_link(deployment_id)

        return (subdomain, short_link)

    def format_url_with_protocol(self, url: str, use_https: bool = True) -> str:
        """
        Add protocol to URL if not present.

        Args:
            url: URL (with or without protocol)
            use_https: Use HTTPS (default) or HTTP

        Returns:
            URL with protocol

        Examples:
            >>> service = VarityURLService()
            >>> service.format_url_with_protocol("my-app.varity.app")
            'https://my-app.varity.app'
        """
        if url.startswith(('http://', 'https://')):
            return url

        protocol = "https" if use_https else "http"
        return f"{protocol}://{url}"


def create_varity_urls(
    deployment_id: str,
    app_name: Optional[str] = None,
    project_type: Optional[str] = None
) -> dict:
    """
    Convenience function to create Varity URLs.

    Args:
        deployment_id: Unique deployment ID
        app_name: Application name (optional)
        project_type: Project type (optional)

    Returns:
        Dictionary with subdomain and short_link URLs

    Examples:
        >>> urls = create_varity_urls("deploy-123", "my-dashboard")
        >>> print(urls['subdomain'])
        'https://my-dashboard-abc123.varity.app'
        >>> print(urls['short_link'])
        'https://varity.app/a/abc123'
    """
    service = VarityURLService()
    subdomain, short_link = service.generate_urls(deployment_id, app_name, project_type)

    return {
        'subdomain': service.format_url_with_protocol(subdomain),
        'short_link': service.format_url_with_protocol(short_link),
        'subdomain_raw': subdomain,
        'short_link_raw': short_link,
    }
