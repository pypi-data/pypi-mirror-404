import os
import sys
from pathlib import Path
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sane_settings import EnvConfigBase, env_field

@dataclass
class TestBoolConfig(EnvConfigBase):
    debug: bool = env_field('TEST_DEBUG', default=True)
    enabled: bool = env_field('TEST_ENABLED', default=False)

def test_bool_default_true():
    # Clear any existing env vars
    os.environ.pop('TEST_DEBUG', None)
    
    config = TestBoolConfig.load_from_env()
    
    # Test that boolean default value is handled correctly
    assert isinstance(config.debug, bool), f"Expected bool, got {type(config.debug)}"
    assert config.debug is True, f"Expected True, got {config.debug}"

def test_bool_default_false():
    # Clear any existing env vars
    os.environ.pop('TEST_ENABLED', None)
    
    config = TestBoolConfig.load_from_env()
    
    # Test that boolean default value is handled correctly
    assert isinstance(config.enabled, bool), f"Expected bool, got {type(config.enabled)}"
    assert config.enabled is False, f"Expected False, got {config.enabled}"

def test_bool_from_env_string():
    # Set env var as string
    os.environ['TEST_DEBUG'] = 'false'
    os.environ['TEST_ENABLED'] = 'true'
    
    config = TestBoolConfig.load_from_env()
    
    # Test that string env vars are properly cast to bool
    assert isinstance(config.debug, bool), f"Expected bool, got {type(config.debug)}"
    assert config.debug is False, f"Expected False, got {config.debug}"
    assert isinstance(config.enabled, bool), f"Expected bool, got {type(config.enabled)}"
    assert config.enabled is True, f"Expected True, got {config.enabled}"
    
    # Clean up
    os.environ.pop('TEST_DEBUG', None)
    os.environ.pop('TEST_ENABLED', None)

if __name__ == "__main__":
    test_bool_default_true()
    test_bool_default_false()
    test_bool_from_env_string()
    print("All tests passed!")