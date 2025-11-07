"""Device utilities for PyTorch models"""

import torch
from typing import Optional
from backend.utils.logging import get_logger

logger = get_logger(__name__)


def get_device(device: Optional[str] = None) -> str:
    """
    Get the appropriate device for PyTorch models.
    
    Args:
        device: Optional device string ("cuda", "cpu", "auto", or None for auto-detect)
        
    Returns:
        Device string ("cuda", "cpu", or "mps")
    """
    if device is not None and device.lower() != "auto":
        # If device is explicitly specified, validate it
        if device.lower() in ("cuda", "cpu", "mps"):
            if device.lower() == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA requested but not available, falling back to CPU")
                return "cpu"
            return device.lower()
        else:
            logger.warning(f"Invalid device '{device}', falling back to auto-detect")
    
    # Auto-detect device
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        logger.info(f"Using CUDA device: {device_name}")
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        logger.info("Using MPS device (Apple Silicon)")
        return "mps"
    else:
        logger.info("CUDA not available, using CPU")
        return "cpu"


def get_torch_device(device: Optional[str] = None) -> torch.device:
    """
    Get a torch.device object for the appropriate device.
    
    Args:
        device: Optional device string ("cuda", "cpu", or None for auto-detect)
        
    Returns:
        torch.device object
    """
    device_str = get_device(device)
    if device_str == "cuda":
        return torch.device("cuda:0")
    elif device_str == "mps":
        return torch.device("mps")
    else:
        return torch.device("cpu")


def is_cuda_available() -> bool:
    """Check if CUDA is available"""
    return torch.cuda.is_available()


def get_cuda_device_count() -> int:
    """Get the number of available CUDA devices"""
    return torch.cuda.device_count() if torch.cuda.is_available() else 0


def get_cuda_device_name(device_id: int = 0) -> Optional[str]:
    """Get the name of a CUDA device"""
    if torch.cuda.is_available() and device_id < torch.cuda.device_count():
        return torch.cuda.get_device_name(device_id)
    return None

