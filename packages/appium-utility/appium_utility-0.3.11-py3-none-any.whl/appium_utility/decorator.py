import inspect
from collections.abc import Callable
from functools import wraps

from selenium.common.exceptions import (InvalidElementStateException, NoSuchElementException,
                                        StaleElementReferenceException, TimeoutException)


def sanitize_action(action: str) -> str:
  return action.replace("_", " ").lower()


class AppiumActionError(RuntimeError):

  def __init__(self, message: str):
    super().__init__(message)

  @classmethod
  def from_action(cls, action: str, message: str) -> "AppiumActionError":
    return cls(f"Failed to {sanitize_action(action)}: {message}")


def unwrap_message(err: AppiumActionError) -> str:
  msg = str(err)
  if msg.startswith("Failed to "):
    return msg.split(":", 1)[1].strip()
  return msg


def map_exception(
  action: str,
  exc: Exception,
  details: str = "",
) -> AppiumActionError:

  if isinstance(exc, NoSuchElementException):
    msg = "element not found"
  elif isinstance(exc, TimeoutException):
    msg = "the operation took too long to complete"
  elif isinstance(exc, StaleElementReferenceException):
    msg = "the screen changed before the action could complete"
  elif isinstance(exc, InvalidElementStateException):
    msg = "the item is not ready for interaction"
  else:
    msg = "an unexpected problem occurred while performing the action"

  if details:
    msg = f"{msg} ({details})"

  return AppiumActionError.from_action(action, msg)


def with_logging(
  action: str,
  details: str | Callable[..., str] | None = None,
):

  def decorator(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):
      details_str = ""

      if details is not None:
        try:
          if isinstance(details, str):
            bound = inspect.signature(fn).bind_partial(*args, **kwargs)
            details_str = details.format(**bound.arguments)
          else:
            details_str = details(*args, **kwargs)
        except Exception:
          details_str = ""

      action_name = sanitize_action(action)

      if details_str:
        print(f"Starting {action_name} ({details_str})")
      else:
        print(f"Starting {action_name}")

      try:
        result = fn(*args, **kwargs)

        print(f"Completed {action_name}")
        return result

      except AppiumActionError as e:
        raise AppiumActionError.from_action(
          action,
          unwrap_message(e),
        ) from e

      except Exception as e:
        raise map_exception(action, e, details_str) from e

    return wrapper

  return decorator
