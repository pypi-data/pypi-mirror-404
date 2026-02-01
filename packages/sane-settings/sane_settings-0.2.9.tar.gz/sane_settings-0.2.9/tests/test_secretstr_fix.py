import os
import sys
from pathlib import Path
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sane_settings import EnvConfigBase, SecretStr, env_field

@dataclass
class TestConfig(EnvConfigBase):
    secret: SecretStr = env_field('TEST_SECRET', default='abc')
    normal_field: str = env_field('TEST_NORMAL', default='def')

def test_secretstr_default():
    # Clear any existing env vars
    os.environ.pop('TEST_SECRET', None)
    os.environ.pop('TEST_NORMAL', None)
    
    config = TestConfig.load_from_env()
    
    # Test that default value is properly cast to SecretStr
    assert isinstance(config.secret, SecretStr), f"Expected SecretStr, got {type(config.secret)}"
    assert config.secret.get_secret_value() == 'abc', f"Expected 'abc', got {config.secret.get_secret_value()}"
    
    # Test that normal field remains as string
    assert isinstance(config.normal_field, str), f"Expected str, got {type(config.normal_field)}"
    assert config.normal_field == 'def', f"Expected 'def', got {config.normal_field}"

def test_secretstr_from_env():
    # Set env var
    os.environ['TEST_SECRET'] = 'xyz'
    os.environ.pop('TEST_NORMAL', None)
    
    config = TestConfig.load_from_env()
    
    # Test that env var value is properly cast to SecretStr
    assert isinstance(config.secret, SecretStr), f"Expected SecretStr, got {type(config.secret)}"
    assert config.secret.get_secret_value() == 'xyz', f"Expected 'xyz', got {config.secret.get_secret_value()}"
    
    # Clean up
    os.environ.pop('TEST_SECRET', None)