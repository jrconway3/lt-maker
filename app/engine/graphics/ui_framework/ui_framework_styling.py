from __future__ import annotations

from enum import Enum

from app.utilities import str_utils


class MetricType(Enum):
  PIXEL = 0
  PERCENTAGE = 1

class UIMetric():
  """A wrapper that handles the two types of length measurement, pixels and percentages, 
  and provides functions that handle, convert, and parse strings into these measurements.
  
  Effectively a barebones substitution of the way CSS handles length measurements.
  """
  def __init__(self, val: int, type: MetricType):
    self.val = int(val)
    self.type = type
    
  def is_pixel(self):
    return self.type == MetricType.PIXEL
  
  def is_percent(self):
    return self.type == MetricType.PERCENTAGE
  
  def to_pixels(self, parent_metric: int = 100):
    if self.is_pixel():
      return self.val
    else:
      return self.val * parent_metric / 100
  
  @classmethod
  def pixels(cls, val):
    return cls(val, MetricType.PIXEL)
  
  @classmethod
  def percent(cls, val):
    return cls(val, MetricType.PERCENTAGE)
  
  @classmethod
  def parse(cls, metric_string):
    """Parses a metric type from some arbitrary given input.
    Basically, "50%" becomes a 50% UIMetric, while all other
    formatting: 50, "50px", "50.0", become 50 pixel UIMetric.

    Args:
        metric_string Union[str, int]: string or integer input

    Returns:
        UIMetric: a UIMetric corresponding to the parsed value
    """
    try:
      if isinstance(metric_string, (float, int)):
        return cls(metric_string, MetricType.PIXEL)
      elif isinstance(metric_string, str):
        if str_utils.is_int(metric_string):
          return cls(int(metric_string), MetricType.PIXEL)
        elif str_utils.is_float(metric_string):
          return cls(int(metric_string), MetricType.PIXEL)
        elif 'px' in metric_string:
          metric_string = metric_string[:-2]
          return cls(int(metric_string), MetricType.PIXEL)
        elif '%' in metric_string:
          metric_string = metric_string[:-1]
          return cls(int(metric_string), MetricType.PERCENTAGE)
    except Exception:
      # the input string was incorrectly formatted
      return cls(0, MetricType.PIXEL)
