import os
from pathlib import Path
from dotenv import load_dotenv, set_key, unset_key, dotenv_values
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    chroma_collection_name: str = "Capabilities"
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from .env to prevent validation errors

    @classmethod
    def get_project_root(cls):
        """Determine the project root directory."""
        script_path = Path(__file__).resolve()
        return script_path.parents[2]  # Adjust the index as needed

    @classmethod
    def load(cls, env_file: str = None):
        """Load environment variables from the specified .env file."""
        env_file = env_file or cls.Config.env_file
        load_dotenv(dotenv_path=env_file)

    @classmethod
    def save(cls, env_file: str = None):
        """Save current settings to the specified .env file."""
        env_file = env_file or cls.Config.env_file
        dotenv_path = Path(env_file)
        if dotenv_path.exists():
            with open(dotenv_path, "w") as f:
                for key, value in cls.dict().items():
                    f.write(f"{key}={value}\n")
        else:
            raise FileNotFoundError(f"{env_file} not found.")

    @classmethod
    def add_or_update(cls, key: str, value: str, env_file: str = None):
        """Add or update a key-value pair in the specified .env file."""
        env_file = env_file or cls.Config.env_file
        dotenv_path = Path(env_file)
        if dotenv_path.exists():
            set_key(dotenv_path, key, value)
        else:
            raise FileNotFoundError(f"{env_file} not found.")

    @classmethod
    def delete(cls, key: str, env_file: str = None):
        """Delete a key-value pair from the specified .env file."""
        env_file = env_file or cls.Config.env_file
        dotenv_path = Path(env_file)
        if dotenv_path.exists():
            unset_key(dotenv_path, key)
        else:
            raise FileNotFoundError(f"{env_file} not found.")

    @classmethod
    def get(cls, key: str, default: str = None, env_file: str = None):
        """Get the value of a key from the specified .env file."""
        env_file = env_file or cls.Config.env_file
        dotenv_path = Path(env_file)
        if dotenv_path.exists():
            return dotenv_values(dotenv_path).get(key, default)
        else:
            error_msg = f"{env_file} not found."
            raise FileNotFoundError(error_msg)

    @classmethod
    def main(cls, env_file: str = None):
        """Load the configuration, manipulate it, and print the settings."""
        env_file = env_file or cls.Config.env_file
        load_dotenv(dotenv_path=env_file)

        # Add a new key-value pair
        set_key(env_file, "FOO", "bar")
        print("After adding FOO=bar:")
        cls.reload_and_print(env_file)

        # Modify the value of the existing key
        set_key(env_file, "FOO", "baz")
        print("\nAfter modifying FOO=bar to FOO=baz:")
        cls.reload_and_print(env_file)

        # Delete the key-value pair
        unset_key(env_file, "FOO")
        print("\nAfter deleting FOO:")
        cls.reload_and_print(env_file)

        # Add new key-value pairs to the .env file
        settings = {
            "FLASK_DEBUG": "False",
            "FLASK_PORT": "5000",
            "GOOGLE_API_KEY": "AIzaSyBQ2fukzcqFLImkJyKESwtP_VOIELHhpmc",
            "GOOGLE_CSE_ID": "a7ce6654d97a94028",
            "HF_TOKEN": "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",
            "LLM_PROVIDER": "openai",
            "LOG_DIR": "{{ PROJECT_ROOT }}/logs",
            "MS_TENANT_ID": "317c1c26-22fe-4b7b-abfa-54aa9952946f",
            "MS_CLIENT_ID": "36fa3e1c-1eac-4f0d-87ae-9651c81d1f42",
            "MS_CLIENT_SECRET": "GJI8Q~SaMNUHnjSfnMYvSAAKDaU.G.WO7QmJYarf"
        }

        for key, value in settings.items():
            set_key(env_file, key, value)
        # Reload and print all settings
        cls.reload_and_print(env_file)

        print(f"CWD = {os.getcwd()}")

    @classmethod
    def reload_and_print(cls, env_file: str):
        """Reload the environment variables and print all key-value pairs."""
        load_dotenv(dotenv_path=env_file)
        config = dotenv_values(env_file)
        for key, value in config.items():
            print(f"{key}={value}")


if __name__ == "__main__":
    AppConfig.main()
