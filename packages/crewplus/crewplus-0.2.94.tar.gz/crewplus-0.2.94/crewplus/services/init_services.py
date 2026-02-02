import logging
import os
from typing import Optional, Dict

from .model_load_balancer import ModelLoadBalancer

model_balancer = None

def init_load_balancer(
    config_path: Optional[str] = None,
    config_data: Optional[Dict] = None,
    logger: Optional[logging.Logger] = None
):
    """
    Initializes the global ModelLoadBalancer instance.

    This function is idempotent. If the balancer is already initialized,
    it does nothing. It follows a safe initialization pattern where the
    global instance is only assigned after successful configuration loading.

    Args:
        config_path (Optional[str]): The path to the model configuration file.
            If not provided, it's determined by the `MODEL_CONFIG_PATH`
            environment variable, or defaults to "config/models_config.json".
            This is ignored if config_data is provided.
        config_data (Optional[Dict]): A dictionary containing the model configuration.
            If provided, this takes precedence over config_path. The dictionary should
            contain a 'models' key with a list of model configurations.
        logger (Optional[logging.Logger]): An optional logger instance to be
            used by the model balancer.
    """
    global model_balancer
    if model_balancer is None:
        # Determine the config source
        final_config_path = None
        if not config_data:
            # Use parameter if provided, otherwise check env var, then default
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_package_dir = os.path.dirname(os.path.dirname(current_dir))
            default_config_path = os.path.join(base_package_dir, "_config", "models_config.json")

            final_config_path = config_path or os.getenv(
                "MODEL_CONFIG_PATH",
                default_config_path
            )

        try:
            # 1. Create a local instance first.
            balancer = ModelLoadBalancer(
                config_path=final_config_path,
                config_data=config_data,
                logger=logger
            )
            # 2. Attempt to load its configuration.
            balancer.load_config()
            # 3. Only assign to the global variable on full success.
            model_balancer = balancer
        except Exception as e:
            # If any step fails, the global model_balancer remains None,
            # allowing for another initialization attempt later.
            # Re-raise the exception to notify the caller of the failure.
            error_source = "config_data" if config_data else final_config_path
            raise RuntimeError(f"Failed to initialize and configure ModelLoadBalancer from {error_source}: {e}") from e

def get_model_balancer() -> ModelLoadBalancer:
    if model_balancer is None:
        raise RuntimeError("ModelLoadBalancer not initialized. Please call init_load_balancer() first.")
    return model_balancer
