"""
Technical Indicators (powered by talipp).

This module exposes "Smart" versions of talipp indicators that handle:
1.  Automatic extraction of `close` price from Candle objects.
2.  Automatic support for `SamplingPeriodType` via efficient internal chaining.
"""

import sys
import inspect
from typing import Any, List, Union
from datetime import datetime

# Import Talipp essentials
from talipp.indicators import *
from talipp.indicators.Indicator import Indicator
from talipp.input import SamplingPeriodType

# 1. Helper: Resampler
class Resampler(Indicator):
    """
    Pass-through indicator that handles sampling.
    """
    def __init__(self, input_sampling):
        super().__init__(input_sampling=input_sampling)
        
    def _calculate_new_value(self):
        # Return the latest aggregated object from the sampler
        if not self.input_values:
            return None
        return self.input_values[-1]

# 2. Smart Wrapper Logic
OHLCV_INDICATORS = {
    "ADX", "ATR", "AccuDist", "Aroon", "BOP", "CCI", "CHOP", "ChaikinOsc",
    "ChandeKrollStop", "DonchianChannels", "EMV", "FibonacciRetracement",
    "ForceIndex", "IBS", "Ichimoku", "KVO", "KeltnerChannels", "MassIndex",
    "NATR", "OBV", "ParabolicSAR", "PivotsHL", "RogersSatchell", "SFX",
    "SOBV", "Stoch", "SuperTrend", "TTM", "UO", "VTX", "VWAP", "VWMA", 
    "Williams", "ZigZag"
}

def _make_smart(cls_name, cls):
    is_ohlcv_native = cls_name in OHLCV_INDICATORS
    
    # We create a wrapper class
    class SmartWrapper(cls):
        def __init__(self, *args, **kwargs):
            # Check for sampling request
            self._resampler = None
            self._is_feeding = False
            
            if 'input_sampling' in kwargs:
                sampling = kwargs.pop('input_sampling')
                
                # Handling Sampling for Float-based indicators (e.g. SMA)
                if not is_ohlcv_native:
                    # Chain: SmartWrapper -> Resampler -> SmartWrapper(Internal Logic)
                    self._resampler = Resampler(input_sampling=sampling)
                    kwargs['input_indicator'] = self._resampler
                    
                    if 'input_modifier' not in kwargs:
                         # Default to Close price for the RETURNED sampled output
                         kwargs['input_modifier'] = lambda c: c.close if hasattr(c, 'close') else c
                else:
                    # OHLCV indicators assume compatible input
                    kwargs['input_sampling'] = sampling
            
            super().__init__(*args, **kwargs)

        def add(self, value: Any):
            # Break recursion: If we are already feeding the resampler (triggered by its own callback),
            # or if we are processing the output of the resampler, proceed to real logic.
            if self._is_feeding:
                super().add(value)
                return

            # If we have a Resampler chain, we must feed the Resampler!
            if self._resampler is not None:
                self._is_feeding = True
                try:
                    self._resampler.add(value)
                finally:
                    self._is_feeding = False
                return 
            
            # Non-sampled, simple mode: Handle conversion manually
            if not is_ohlcv_native:
                if hasattr(value, 'close'):
                    value = value.close
            
            super().add(value)
            
    try:
        SmartWrapper.__name__ = cls_name
        SmartWrapper.__doc__ = cls.__doc__
    except:
        pass
        
    return SmartWrapper

# Re-export all indicators as SmartWrappers
import talipp.indicators as _ti

msg = []

for name, obj in inspect.getmembers(_ti):
    if inspect.isclass(obj) and obj.__module__.startswith('talipp'):
        # Create smart wrapper
        SmartObj = _make_smart(name, obj)
        # Export it
        setattr(sys.modules[__name__], name, SmartObj)
        msg.append(name)

__all__ = msg + ["SamplingPeriodType"]
