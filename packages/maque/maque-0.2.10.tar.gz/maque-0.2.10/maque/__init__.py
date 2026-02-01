__version__ = "0.2.10"

from .io import (
    yaml_load,
    yaml_dump,
    save,
    load,
    json_load,
    json_dump,
    jsonl_load,
    jsonl_dump,
)
from .utils.path import rel_to_abs, rel_path_join, ls, add_env_path
relp = rel_to_abs  # alias
from .performance import MeasureTime
from .nlp.parser import parse_to_obj, parse_to_code
from .ai_platform.metrics import MetricsCalculator, export_eval_report, save_pred_metrics

# Import with optional dependencies (from flexllm)
try:
    from flexllm.processors.image_processor import ImageCacheConfig
    from flexllm.processors.image_processor_helper import ImageProcessor

    from flexllm import MllmClient, LLMClient, ResponseCacheConfig
    from flexllm.openaiclient import OpenAIClient
    from flexllm.geminiclient import GeminiClient
    from flexllm.processors.unified_processor import batch_process_messages, messages_preprocess

except ImportError:
    pass
