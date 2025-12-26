import json
from typing import Any
from typing import Optional, List
from fastapi import HTTPException, APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/config",
    tags=["Config"]
)

# --- Configuration ---
CONFIG_FILE_PATH = "config.json"

# --- Pydantic Models For API Data ---
class ConfigJsonItem(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    endpoint: Optional[str] = None
    apiKey: Optional[str] = None
    
class Config(BaseModel):
    provider: str
    isSelected: bool
    configJson: ConfigJsonItem

# --- Settings Service ---
class SettingsService:
    def __init__(self):
        self.config: Optional[List[Config]] = None
        self._llm_cache = None
        self._current_provider = None

    def _find_provider(self, provider_name: str) -> Optional[Config]:
        config = self.get_configs()
        return next((provider for provider in config if provider.provider == provider_name), None)

    def _find_selected(self) -> Optional[Config]:
        config = self.get_configs()
        return next((provider for provider in config if provider.isSelected), None)
    
    def _read_config(self) -> List[Config]:
        try:
            with open(CONFIG_FILE_PATH, "r") as f:
                config_data = json.load(f)
            return [Config(**item) for item in config_data]
        except (OSError, IOError, json.JSONDecodeError) as e:
            raise HTTPException(status_code=500, detail=f"Error reading config: {e}")
    
    def _save_config(self, config: List[Config]) -> None:
        try:
            with open(CONFIG_FILE_PATH, "w") as f:
                json.dump([config_item.dict() for config_item in config], f, indent=2)
            self.config = config
        except (OSError, IOError, TypeError) as e:
            raise HTTPException(status_code=500, detail=f"Error saving config: {e}")

    def get_configs(self) -> List[Config]:
        if not self.config:
            self.config = self._read_config()
        return self.config

    def get_provider_config(self, provider_name: str) -> Config:
        provider_config = self._find_provider(provider_name)
        if provider_config:
            return provider_config
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

    def set_default_provider(self, provider_name: str) -> None:
        config = self.get_configs()
        for provider_config in config:
            provider_config.isSelected = False
        selected_provider = self._find_provider(provider_name)
        if selected_provider:
            selected_provider.isSelected = True
            self._save_config(config)
        else:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

    def update_provider_config(self, provider_name: str, new_config_json: ConfigJsonItem) -> None:
        provider_config = self._find_provider(provider_name)
        if provider_config:
            provider_config.configJson = new_config_json
            self._save_config(self.get_configs())
        else:
            raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

    def get_selected_config(self) -> Config:
        selected_config = self._find_selected()
        if selected_config:
            return selected_config
        raise HTTPException(status_code=404, detail="No provider is selected")
    
    def _get_llm(self) -> Any:
        """
        Factory method to create the appropriate LLM client based on the selected provider.
        Returns the initialized LLM client ready for use.
        """
        selected_config = self.get_selected_config()
        provider = selected_config.provider
        config_json = selected_config.configJson
        
        if provider == "Ollama":
            from langchain_ollama.llms import OllamaLLM
            return OllamaLLM(model=config_json.model)
        
        elif provider == "GROQ":
            from langchain_groq import ChatGroq
            return ChatGroq(
                api_key=config_json.apiKey,
                model=config_json.model,
                temperature=0.2
            )
        
        elif provider == "AWS":
            from langchain_aws import BedrockLLM
            return BedrockLLM(
                model_id=config_json.model,
                credentials_profile_name="default",
                endpoint_url=config_json.endpoint
            )
        
        elif provider == "Azure":
            from langchain_openai import AzureChatOpenAI
            return AzureChatOpenAI(
                azure_endpoint=config_json.endpoint,
                api_key=config_json.apiKey,
                azure_deployment=config_json.model
            )
        
        elif provider == "GCP":
            from langchain_google_vertexai import ChatVertexAI
            return ChatVertexAI(
                model=config_json.model
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    def get_cached_llm(self) -> Any:
        """
        Returns a cached LLM instance for the currently selected provider.
        Re-initializes if the provider changes.
        """
        selected_config = self.get_selected_config()
        current_provider = selected_config.provider

        if self._llm_cache is None or self._current_provider != current_provider:
            self._llm_cache = self._get_llm()
            self._current_provider = current_provider
            print(f"Initialized LLM for provider: {current_provider}")

        return self._llm_cache

settings_service = SettingsService()

# --- API Endpoints ---

# Get Config
@router.get("/", response_model=List[Config])
def get_config():
    try:
        return settings_service.get_configs()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

# Set Config
@router.post("/{provider_name}", response_model=Config)
def set_default_provider(provider_name: str):
    settings_service.set_default_provider(provider_name)
    return settings_service.get_provider_config(provider_name)

# Update Config
@router.put("/{provider_name}", response_model=Config)
def update_provider_config(provider_name: str, new_config_json: ConfigJsonItem):
    settings_service.update_provider_config(provider_name, new_config_json)
    return settings_service.get_provider_config(provider_name)
