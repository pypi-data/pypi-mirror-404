"""
ISAF Decorators for automatic compliance logging.

Provides decorators to capture Layer 6 (Framework), Layer 7 (Data),
Layer 8 (Objective), and Layer 9 (Deployment/Inference) information
from AI training and inference code.
"""

import functools
import inspect
import hashlib
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from datetime import datetime

logger = logging.getLogger('isaf')

F = TypeVar('F', bound=Callable[..., Any])


def _safe_get_source(func: Callable) -> Optional[str]:
    """Safely extract source code from a function."""
    try:
        return inspect.getsource(func)
    except (OSError, TypeError):
        return None


def _extract_arg_info(func: Callable, args: tuple, kwargs: dict) -> Dict[str, Any]:
    """Extract argument names and values from function call."""
    sig = inspect.signature(func)
    bound = sig.bind(*args, **kwargs)
    bound.apply_defaults()
    
    result = {}
    for name, value in bound.arguments.items():
        try:
            if hasattr(value, 'shape'):
                result[name] = {'type': type(value).__name__, 'shape': str(value.shape)}
            elif hasattr(value, '__len__') and not isinstance(value, str):
                result[name] = {'type': type(value).__name__, 'length': len(value)}
            else:
                result[name] = {'type': type(value).__name__, 'value': str(value)[:100]}
        except Exception:
            result[name] = {'type': type(value).__name__}
    
    return result


def _is_data_like(obj: Any) -> bool:
    """Check if object looks like training data."""
    if obj is None:
        return False
    
    type_name = type(obj).__name__.lower()
    data_types = ['dataframe', 'ndarray', 'tensor', 'dataset', 'dataloader']
    
    if any(dt in type_name for dt in data_types):
        return True
    
    if hasattr(obj, 'shape') or hasattr(obj, '__len__'):
        return True
    
    return False


def _compute_data_hash(data: Any) -> Optional[str]:
    """Compute a hash of the data for provenance tracking."""
    try:
        if hasattr(data, 'tobytes'):
            return hashlib.sha256(data.tobytes()[:10000]).hexdigest()[:16]
        elif hasattr(data, 'values'):
            return hashlib.sha256(str(data.values[:100]).encode()).hexdigest()[:16]
        else:
            return hashlib.sha256(str(data)[:1000].encode()).hexdigest()[:16]
    except Exception:
        return None


def log_objective(
    name: Optional[str] = None,
    constraints: Optional[List[str]] = None,
    justification: Optional[str] = None
) -> Callable[[F], F]:
    """
    Decorator to log Layer 8 (Objective Function) information.
    
    Args:
        name: Name of the objective/loss function
        constraints: List of constraints or regularization terms
        justification: Business justification for this objective
    
    Example:
        @isaf.log_objective(name="cross_entropy", constraints=["L2_reg"])
        def train(model, data):
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from isaf.core.session import get_session
            from isaf.core.extractors import Layer8Extractor
            
            session = get_session()
            if session is None:
                return func(*args, **kwargs)
            
            try:
                context = {
                    'function_name': func.__name__,
                    'module': func.__module__,
                    'source_code': _safe_get_source(func),
                    'arguments': _extract_arg_info(func, args, kwargs),
                    'objective_name': name or func.__name__,
                    'constraints': constraints or [],
                    'justification': justification,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                extractor = Layer8Extractor()
                layer_data = extractor.extract(context)
                session.log_layer(8, layer_data)
                
            except Exception as e:
                logger.warning(f"Failed to log Layer 8 (Objective) for {func.__name__}: {e}")

            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def log_data(
    source: Optional[str] = None,
    version: Optional[str] = None,
    **metadata: Any
) -> Callable[[F], F]:
    """
    Decorator to log Layer 7 (Training Data) information.
    
    Args:
        source: Data source identifier (e.g., "internal", "public", "vendor")
        version: Data version string
        **metadata: Additional metadata to log
    
    Example:
        @isaf.log_data(source="internal", version="2024-01")
        def load_training_data():
            return pd.read_csv("data.csv")
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from isaf.core.session import get_session
            from isaf.core.extractors import Layer7Extractor
            
            result = func(*args, **kwargs)
            
            session = get_session()
            if session is None:
                return result
            
            try:
                context = {
                    'function_name': func.__name__,
                    'module': func.__module__,
                    'source': source,
                    'version': version,
                    'metadata': metadata,
                    'returned_data': result,
                    'data_hash': _compute_data_hash(result),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                extractor = Layer7Extractor()
                layer_data = extractor.extract(context)
                session.log_layer(7, layer_data)
                
            except Exception as e:
                logger.warning(f"Failed to log Layer 7 (Data) for {func.__name__}: {e}")

            return result

        return wrapper  # type: ignore

    return decorator


def log_framework(func: Optional[F] = None) -> Union[F, Callable[[F], F]]:
    """
    Decorator to log Layer 6 (Framework) information.
    
    Automatically detects PyTorch, TensorFlow, JAX, or scikit-learn
    and logs framework configuration, versions, and defaults.
    
    Example:
        @isaf.log_framework
        def build_model():
            return torch.nn.Sequential(...)
    """
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            from isaf.core.session import get_session
            from isaf.core.extractors import Layer6Extractor
            
            session = get_session()
            if session is None:
                return fn(*args, **kwargs)
            
            try:
                context = {
                    'function_name': fn.__name__,
                    'module': fn.__module__,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                extractor = Layer6Extractor()
                layer_data = extractor.extract(context)
                session.log_layer(6, layer_data)
                
            except Exception as e:
                logger.warning(f"Failed to log Layer 6 (Framework) for {fn.__name__}: {e}")

            return fn(*args, **kwargs)

        return wrapper  # type: ignore

    if func is not None:
        return decorator(func)
    
    return decorator


def log_all(func: F) -> F:
    """
    Convenience decorator that logs all available layers.
    
    Logs Layer 6 (Framework) automatically, and attempts to log
    Layer 7 (Data) if the function returns data-like objects.
    
    Example:
        @isaf.log_all
        def train_pipeline():
            data = load_data()
            model = build_model()
            train(model, data)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from isaf.core.session import get_session
        from isaf.core.extractors import Layer6Extractor, Layer7Extractor
        
        session = get_session()
        if session is None:
            return func(*args, **kwargs)
        
        try:
            context = {
                'function_name': func.__name__,
                'module': func.__module__,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            extractor6 = Layer6Extractor()
            layer6_data = extractor6.extract(context)
            session.log_layer(6, layer6_data)

        except Exception as e:
            logger.warning(f"Failed to log Layer 6 (Framework) in log_all for {func.__name__}: {e}")

        result = func(*args, **kwargs)
        
        if _is_data_like(result):
            try:
                context = {
                    'function_name': func.__name__,
                    'module': func.__module__,
                    'returned_data': result,
                    'data_hash': _compute_data_hash(result),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                extractor7 = Layer7Extractor()
                layer7_data = extractor7.extract(context)
                session.log_layer(7, layer7_data)

            except Exception as e:
                logger.warning(f"Failed to log Layer 7 (Data) in log_all for {func.__name__}: {e}")

        return result

    return wrapper  # type: ignore


def log_inference(
    threshold: Optional[float] = None,
    thresholds: Optional[Dict[str, float]] = None,
    model_version: Optional[str] = None,
    model_name: Optional[str] = None,
    human_oversight: bool = False,
    review_threshold: Optional[float] = None,
    fallback_action: str = 'reject',
    inference_mode: str = 'single',
    **config: Any
) -> Callable[[F], F]:
    """
    Decorator to log Layer 9 (Deployment/Inference) information.

    Captures inference configuration, decision thresholds, and human oversight
    settings for EU AI Act Article 14 compliance.

    Args:
        threshold: Decision threshold for binary classification (0.0-1.0)
        thresholds: Dictionary of thresholds for multi-class {class_name: threshold}
        model_version: Version of the model being used for inference
        model_name: Name/identifier of the model
        human_oversight: Enable human oversight logging
        review_threshold: Confidence threshold below which human review is required
        fallback_action: Action when confidence is below threshold ('reject', 'flag', 'default')
        inference_mode: Type of inference ('single', 'batch', 'streaming')
        **config: Additional inference configuration

    Example:
        @isaf.log_inference(threshold=0.5, model_version="1.2.0", human_oversight=True)
        def predict(input_data):
            return model(input_data)

        @isaf.log_inference(
            thresholds={'positive': 0.7, 'negative': 0.3},
            review_threshold=0.6,
            human_oversight=True
        )
        def classify(text):
            return classifier.predict(text)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            from isaf.core.session import get_session
            from isaf.core.extractors import Layer9Extractor

            # Execute the inference function first
            result = func(*args, **kwargs)

            session = get_session()
            if session is None:
                return result

            try:
                # Extract input/output information
                input_info = _extract_inference_io(args, kwargs)
                output_info = _extract_output_info(result)

                context = {
                    'function_name': func.__name__,
                    'module': func.__module__,
                    'threshold': threshold,
                    'thresholds': thresholds or {},
                    'model_version': model_version,
                    'model_name': model_name,
                    'human_oversight': human_oversight,
                    'review_threshold': review_threshold,
                    'fallback_action': fallback_action,
                    'inference_mode': inference_mode,
                    'input_schema': input_info,
                    'output_schema': output_info,
                    'timestamp': datetime.utcnow().isoformat(),
                    **config
                }

                extractor = Layer9Extractor()
                layer_data = extractor.extract(context)
                session.log_layer(9, layer_data)

            except Exception as e:
                logger.warning(f"Failed to log Layer 9 (Inference) for {func.__name__}: {e}")

            return result

        return wrapper  # type: ignore

    return decorator


def _extract_inference_io(args: tuple, kwargs: dict) -> Dict[str, Any]:
    """Extract input information for inference logging."""
    input_info = {}

    # Analyze first positional argument (usually the input data)
    if args:
        first_arg = args[0]
        input_info['type'] = type(first_arg).__name__
        if hasattr(first_arg, 'shape'):
            input_info['shape'] = list(first_arg.shape)
        elif hasattr(first_arg, '__len__'):
            try:
                input_info['length'] = len(first_arg)
            except Exception:
                pass

    return input_info


def _extract_output_info(result: Any) -> Dict[str, Any]:
    """Extract output information from inference result."""
    output_info = {
        'type': type(result).__name__
    }

    if hasattr(result, 'shape'):
        output_info['shape'] = list(result.shape)

    # Try to extract confidence scores
    if hasattr(result, 'max'):
        try:
            output_info['max_confidence'] = float(result.max())
        except Exception:
            pass

    if hasattr(result, '__len__'):
        try:
            output_info['length'] = len(result)
        except Exception:
            pass

    return output_info
