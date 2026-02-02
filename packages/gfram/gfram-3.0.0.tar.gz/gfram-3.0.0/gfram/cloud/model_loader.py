"""
GFRAM Model Loader
==================

Auto-download model from https://gfram.uz

Author: Ortiqova F.S.
"""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_model_path() -> Path:
    """Get model path in cache"""
    from .server_client import get_cache_dir
    return get_cache_dir() / 'gfram_model.pth'


def ensure_model_available(force_download: bool = False) -> Optional[Path]:
    """
    Ensure model is available, download if needed.
    
    Args:
        force_download: Force re-download
    
    Returns:
        Path to model or None
    """
    model_path = get_model_path()
    
    # Check cache
    if model_path.exists() and not force_download:
        logger.info(f"Model in cache: {model_path}")
        return model_path
    
    # Try to download from server
    try:
        from .server_client import download_model
        
        downloaded = download_model(force=force_download)
        if downloaded and downloaded.exists():
            return downloaded
            
    except Exception as e:
        logger.warning(f"Could not download: {e}")
    
    # Fallback: local model in package
    local_paths = [
        Path(__file__).parent.parent / 'pretrained' / 'gfram_v3.0.0_pretrained.pth',
        Path(__file__).parent.parent / 'pretrained' / 'gfram_model.pth',
    ]
    
    for path in local_paths:
        if path.exists():
            logger.info(f"Using local model: {path}")
            return path
    
    logger.warning("No model found!")
    return None


def clear_cache():
    """Clear model cache"""
    from .server_client import get_cache_dir
    
    cache_dir = get_cache_dir()
    
    for f in cache_dir.glob('*.pth'):
        f.unlink()
        logger.info(f"Deleted: {f}")
    
    print(f"✅ Cache cleared: {cache_dir}")
