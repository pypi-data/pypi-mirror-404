"""
CosyVoice: Text-to-Speech with Large Language Model
"""

__version__ = "0.1.0"

# Lazy import to avoid requiring all dependencies at package import time
def __getattr__(name):
    if name in ('CosyVoice', 'CosyVoice2'):
        from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2
        if name == 'CosyVoice':
            return CosyVoice
        elif name == 'CosyVoice2':
            return CosyVoice2
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ['CosyVoice', 'CosyVoice2']
