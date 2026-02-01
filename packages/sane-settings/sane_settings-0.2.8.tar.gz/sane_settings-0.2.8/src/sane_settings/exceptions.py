import os# Custom exceptions remain the same
import os

class MissingEnvVarError(Exception):
    def __init__(self, full_env_var_name: str, name: str):
        self.full_env_var_name = full_env_var_name
        self.name = name
        env_vars = "\nAvailable environment variables:\n" + "\n".join(f"  - {key}" for key in os.environ.keys())
        super().__init__(f"Required environment variable '{full_env_var_name}' is not set for attribute '{name}'.\n{env_vars}")


class InvalidTypeError(Exception):
    pass


