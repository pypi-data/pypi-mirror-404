"""
Configuration management for S3Hero.

Supports multiple profiles for different S3 providers.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .client import S3Config, S3Provider


# Default config file location
DEFAULT_CONFIG_DIR = Path.home() / ".s3hero"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"


@dataclass
class Profile:
    """A configuration profile for S3 connection."""
    name: str
    provider: S3Provider
    access_key: str
    secret_key: str
    region: str = "us-east-1"
    endpoint_url: Optional[str] = None
    account_id: Optional[str] = None  # For Cloudflare R2
    default_bucket: Optional[str] = None

    def to_s3_config(self) -> S3Config:
        """Convert profile to S3Config."""
        return S3Config(
            provider=self.provider,
            access_key=self.access_key,
            secret_key=self.secret_key,
            region=self.region,
            endpoint_url=self.endpoint_url,
            account_id=self.account_id
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization."""
        return {
            'name': self.name,
            'provider': self.provider.value,
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'region': self.region,
            'endpoint_url': self.endpoint_url,
            'account_id': self.account_id,
            'default_bucket': self.default_bucket
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create profile from dictionary."""
        provider_str = data.get('provider', 'aws')
        provider = S3Provider(provider_str)
        
        return cls(
            name=data['name'],
            provider=provider,
            access_key=data['access_key'],
            secret_key=data['secret_key'],
            region=data.get('region', 'us-east-1'),
            endpoint_url=data.get('endpoint_url'),
            account_id=data.get('account_id'),
            default_bucket=data.get('default_bucket')
        )


@dataclass
class ConfigManager:
    """Manages S3Hero configuration and profiles."""
    config_file: Path = field(default_factory=lambda: DEFAULT_CONFIG_FILE)
    profiles: Dict[str, Profile] = field(default_factory=dict)
    default_profile: Optional[str] = None

    def __post_init__(self) -> None:
        """Load configuration if file exists."""
        if self.config_file.exists():
            self.load()

    def load(self) -> None:
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            self.default_profile = data.get('default_profile')
            self.profiles = {}
            
            for profile_data in data.get('profiles', []):
                profile = Profile.from_dict(profile_data)
                self.profiles[profile.name] = profile
        except Exception as e:
            raise ConfigError(f"Failed to load config: {e}")

    def save(self) -> None:
        """Save configuration to file."""
        try:
            # Create config directory if needed
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'default_profile': self.default_profile,
                'profiles': [p.to_dict() for p in self.profiles.values()]
            }
            
            with open(self.config_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            
            # Set restrictive permissions on config file (contains secrets)
            os.chmod(self.config_file, 0o600)
        except Exception as e:
            raise ConfigError(f"Failed to save config: {e}")

    def add_profile(self, profile: Profile, set_default: bool = False) -> None:
        """Add or update a profile."""
        self.profiles[profile.name] = profile
        
        if set_default or len(self.profiles) == 1:
            self.default_profile = profile.name
        
        self.save()

    def remove_profile(self, name: str) -> bool:
        """Remove a profile."""
        if name in self.profiles:
            del self.profiles[name]
            
            if self.default_profile == name:
                self.default_profile = next(iter(self.profiles), None)
            
            self.save()
            return True
        return False

    def get_profile(self, name: Optional[str] = None) -> Optional[Profile]:
        """Get a profile by name, or the default profile."""
        if name:
            return self.profiles.get(name)
        
        if self.default_profile:
            return self.profiles.get(self.default_profile)
        
        return None

    def list_profiles(self) -> List[Profile]:
        """List all profiles."""
        return list(self.profiles.values())

    def set_default(self, name: str) -> bool:
        """Set the default profile."""
        if name in self.profiles:
            self.default_profile = name
            self.save()
            return True
        return False

    def profile_exists(self, name: str) -> bool:
        """Check if a profile exists."""
        return name in self.profiles


def get_config_manager(config_file: Optional[Path] = None) -> ConfigManager:
    """Get a ConfigManager instance."""
    if config_file:
        return ConfigManager(config_file=config_file)
    return ConfigManager()


def create_profile_interactive() -> Profile:
    """Create a profile interactively (used by CLI)."""
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    
    console = Console()
    
    console.print("\n[bold cyan]S3Hero Profile Setup[/bold cyan]\n")
    
    # Get profile name
    name = Prompt.ask("Profile name", default="default")
    
    # Select provider
    console.print("\nSelect S3 Provider:")
    console.print("  [bold]1.[/bold] AWS S3")
    console.print("  [bold]2.[/bold] Cloudflare R2")
    console.print("  [bold]3.[/bold] Other S3-Compatible")
    
    provider_choice = Prompt.ask("Provider", choices=["1", "2", "3"], default="1")
    
    provider_map = {
        "1": S3Provider.AWS,
        "2": S3Provider.CLOUDFLARE_R2,
        "3": S3Provider.OTHER
    }
    provider = provider_map[provider_choice]
    
    # Get credentials
    access_key = Prompt.ask("Access Key ID")
    secret_key = Prompt.ask("Secret Access Key", password=True)
    
    # Provider-specific options
    region = "us-east-1"
    endpoint_url = None
    account_id = None
    
    if provider == S3Provider.CLOUDFLARE_R2:
        account_id = Prompt.ask("Cloudflare Account ID")
        region = "auto"
    elif provider == S3Provider.OTHER:
        endpoint_url = Prompt.ask("Endpoint URL (e.g., https://s3.example.com)")
        region = Prompt.ask("Region", default="us-east-1")
    else:  # AWS
        region = Prompt.ask("AWS Region", default="us-east-1")
    
    # Optional default bucket
    default_bucket = None
    if Confirm.ask("Set a default bucket?", default=False):
        default_bucket = Prompt.ask("Default bucket name")
    
    return Profile(
        name=name,
        provider=provider,
        access_key=access_key,
        secret_key=secret_key,
        region=region,
        endpoint_url=endpoint_url,
        account_id=account_id,
        default_bucket=default_bucket
    )


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass
