import re
import string
import time
from collections.abc import Callable
from random import choice
from typing import Any, Literal

from appium.webdriver import WebElement as MobileWebElement
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import WebDriver
from selenium.common.exceptions import (InvalidElementStateException, NoSuchElementException,
                                        StaleElementReferenceException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.pointer_input import PointerInput

from appium_utility.decorator import AppiumActionError, with_logging


class AppiumUtility:

  def __init__(self, driver: WebDriver):
    self.driver = driver
    self.focus_elem_retries = 5
    self.focus_elem_delay = 1
    self.fake = Faker()

  @with_logging("LAUNCH APP", "app id='{app_id}'")
  def launch_app(self, app_id: str):
    self.driver.activate_app(app_id)

  @with_logging("PRESS KEY", "key='{key}'")
  def press_key(self, key: str):
    key_map = {
      "home": 3,
      "back": 4,
      "enter": 66,
      "backspace": 67,
    }
    if key not in key_map:
      raise AppiumActionError(f"the key '{key}' is not supported", )
    self.driver.press_keycode(key_map[key])

  @with_logging("HIDE KEYBOARD")
  def hide_keyboard(self):
    self.driver.hide_keyboard()

  def sleep(self, seconds: float):
    time.sleep(seconds)

  @with_logging("CLICK BY TEXT", "text='{text}'")
  def click_by_text(self, text: str, regex: bool = False):
    el = self._find_by_text(text, regex)
    self._click_element(el, "CLICK BY TEXT")

  @with_logging("CLICK BY ID", "id='{resource_id}'")
  def click_by_id(self, resource_id: str):
    el = self._find_by_id(resource_id)
    self._click_element(el, "CLICK BY ID")

  @with_logging("CLICK BY DESCRIPTION", "description='{content_desc}'")
  def click_by_content_desc(self, content_desc: str, regex: bool = False):
    el = self._find_by_desc(content_desc, regex)
    self._click_element(el, "CLICK BY DESCRIPTION")

  @with_logging("CLICK BY XPATH", "xpath='{xpath}'")
  def click_by_xpath(self, xpath: str):
    el = self._find_by_xpath(xpath)
    self._click_element(el, "CLICK BY XPATH")

  @with_logging("CLICK BY SCREEN POSITION", "x={x_percent}, y={y_percent}")
  def click_by_percent(self, x_percent: float, y_percent: float):
    size = self.driver.get_window_size()
    x = int(size["width"] * x_percent)
    y = int(size["height"] * y_percent)

    try:
      finger = PointerInput("touch", "finger")
      actions = ActionChains(self.driver)
      actions.w3c_actions.devices = [finger]

      finger.create_pointer_move(x=x, y=y)
      finger.create_pointer_down()
      finger.create_pointer_up(button=0)

      actions.perform()
    except Exception as e:
      raise AppiumActionError.from_action(
        "CLICK BY SCREEN POSITION",
        "the tap action could not be performed on the screen",
      ) from e

  @with_logging("ENTER TEXT", "value='{text}'")
  def input_text(self, text: str):
    self._with_focused_element_and_retry(
      self.focus_elem_retries,
      self.focus_elem_delay,
      lambda el: el.send_keys(text),
    )

  @with_logging("CLEAR TEXT")
  def erase_text(self):
    self._with_focused_element_and_retry(
      self.focus_elem_retries,
      self.focus_elem_delay,
      lambda el: el.clear(),
    )

  @with_logging("SWIPE", "from ({start_x},{start_y}) to ({end_x},{end_y})")
  def swipe_percent(self, start_x, start_y, end_x, end_y, duration=300):
    size = self.driver.get_window_size()
    sx = int(size["width"] * start_x)
    sy = int(size["height"] * start_y)
    ex = int(size["width"] * end_x)
    ey = int(size["height"] * end_y)

    try:
      self._swipe_points(sx, sy, ex, ey, duration)
    except Exception as e:
      raise AppiumActionError.from_action(
        "SWIPE",
        "the swipe gesture could not be completed",
      ) from e

  def _swipe_points(
    self,
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration=300,
  ):

    finger = PointerInput("touch", "finger")
    actions = ActionChains(self.driver)
    actions.w3c_actions.devices = [finger]

    finger.create_pointer_move(duration=0, x=start_x, y=start_y)
    finger.create_pointer_down()
    finger.create_pointer_move(duration=duration, x=end_x, y=end_y)
    finger.create_pointer_up(button=0)

    actions.perform()

  def swipe_up(self, duration=300):
    size = self.driver.get_window_size()
    x = int(size["width"]) // 2
    start_y = int(size["height"]) // 3
    end_y = start_y // 2
    self._swipe_points(x, start_y, x, end_y, duration)

  def swipe_down(self, duration=300):
    size = self.driver.get_window_size()
    x = int(size["width"]) // 2
    end_y = int(size["height"]) // 3
    start_y = end_y // 2
    self._swipe_points(x, start_y, x, end_y, duration)

  @with_logging("VERIFY TEXT IS VISIBLE", "text='{text}'")
  def assert_text_visible(self, text: str, regex: bool = False):
    if not self._finds_by_text(text, regex):
      raise AppiumActionError(f"the text '{text}' is not present on the screen")

  @with_logging("VERIFY TEXT IS NOT VISIBLE", "text='{text}'")
  def assert_text_not_visible(self, text: str, regex: bool = False):
    if self._finds_by_text(text, regex):
      raise AppiumActionError(f"the text '{text}' is present on the screen")

  @with_logging("SWIPE UNTIL TEXT VISIBLE", "text='{text}', direction='{direction}'")
  def swipe_until_text_visible(
    self,
    text: str,
    direction: Literal["SWIPE_UP", "SWIPE_DOWN"],
    duration=300,
    max_swipes: int = 10,
  ):
    for _ in range(max_swipes):
      time.sleep(0.8)  # wait for the screen to stabilize after swipe
      try:
        self._find_by_text(text, regex=True)
        return
      except AppiumActionError:
        if direction == "SWIPE_UP":
          self.swipe_up(duration)
        elif direction == "SWIPE_DOWN":
          self.swipe_down(duration)
        else:
          raise AppiumActionError(f"invalid swipe direction '{direction}'")

    raise AppiumActionError.from_action(
      "SWIPE UNTIL TEXT VISIBLE",
      f"text '{text}' not found after {max_swipes} swipes",
    )

  @with_logging("SWIPE UNTIL DESCRIPTION VISIBLE",
                "description='{content_desc}', direction='{direction}'")
  def swipe_until_content_desc_visible(
    self,
    content_desc: str,
    direction: Literal["SWIPE_UP", "SWIPE_DOWN"],
    duration=300,
    max_swipes: int = 10,
  ):
    for _ in range(max_swipes):
      time.sleep(0.8)  # wait for the screen to stabilize after swipe
      try:
        self._find_by_desc(content_desc, regex=True)
        return
      except AppiumActionError:
        if direction == "SWIPE_UP":
          self.swipe_up(duration)
        elif direction == "SWIPE_DOWN":
          self.swipe_down(duration)
        else:
          raise AppiumActionError(f"invalid swipe direction '{direction}'")

    raise AppiumActionError.from_action(
      "SWIPE UNTIL DESCRIPTION VISIBLE",
      f"description '{content_desc}' not found after {max_swipes} swipes",
    )

  def _find_by_id(self, resource_id: str):
    try:
      return self.driver.find_element(AppiumBy.ID, resource_id)
    except NoSuchElementException as e:
      raise AppiumActionError.from_action(
        "FIND BY ID",
        f"element not found (id='{resource_id}')",
      ) from e

  def _find_by_text(self, text: str, regex: bool):
    selector = (f'new UiSelector().textMatches("{text}")'
                if regex else f'new UiSelector().textContains("{text}")')
    try:
      elems = self.driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        selector,
      )
      if not elems:
        raise NoSuchElementException()

      return select_one_elem(
        elems,
        get_match_score=lambda el: _cal_match_score(el.text, text, regex),
      )
    except NoSuchElementException as e:
      raise AppiumActionError.from_action(
        "FIND BY TEXT",
        f"text not found (text='{text}')",
      ) from e

  def _find_by_desc(self, text: str, regex: bool):
    selector = (f'new UiSelector().descriptionMatches("{text}")'
                if regex else f'new UiSelector().descriptionContains("{text}")')
    try:
      elems = self.driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        selector,
      )
      if not elems:
        raise NoSuchElementException()

      return select_one_elem(
        elems,
        get_match_score=lambda el: _cal_match_score(
          el.get_attribute("content-desc"),  # type: ignore
          text,
          regex,
        ),
      )
    except NoSuchElementException as e:
      raise AppiumActionError.from_action(
        "FIND BY DESCRIPTION",
        f"description not found (description='{text}')",
      ) from e

  def _find_by_xpath(self, xpath: str):
    try:
      return self.driver.find_element(AppiumBy.XPATH, xpath)
    except NoSuchElementException as e:
      raise AppiumActionError.from_action(
        "FIND BY XPATH",
        f"element not found (xpath='{xpath}')",
      ) from e

  def _finds_by_text(self, text: str, regex: bool):
    selector = (f'new UiSelector().textMatches("{text}")'
                if regex else f'new UiSelector().textContains("{text}")')
    return self.driver.find_elements(
      AppiumBy.ANDROID_UIAUTOMATOR,
      selector,
    )

  def _click_element(self, el, action_name: str):
    try:
      el.click()
    except StaleElementReferenceException as e:
      raise AppiumActionError.from_action(
        action_name,
        "screen changed before the action completed",
      ) from e
    except InvalidElementStateException as e:
      raise AppiumActionError.from_action(
        action_name,
        "the element is not ready for interaction",
      ) from e

  def _find_focused_input_element(self):
    elems = self.driver.find_elements(
      AppiumBy.ANDROID_UIAUTOMATOR,
      "new UiSelector().focused(true)",
    )

    for el in elems:
      if el.get_attribute("class") in (
          "android.widget.EditText",
          "android.widget.TextView",
      ):
        return el

    raise AppiumActionError.from_action(
      "FOCUS INPUT FIELD",
      "no editable input field is currently focused",
    )

  def _with_focused_element_and_retry(
    self,
    retries: int,
    delay: float,
    func: Callable[[Any], Any],
  ):

    for _ in range(retries):
      try:
        el = self._find_focused_input_element()
        return func(el)
      except (
          AppiumActionError,
          NoSuchElementException,
          StaleElementReferenceException,
          InvalidElementStateException,
      ):
        time.sleep(delay)

    raise AppiumActionError.from_action(
      "FOCUS INPUT FIELD",
      "input field not ready after multiple attempts",
    )


def select_one_elem(
  elems: list[MobileWebElement],
  get_match_score: Callable[[MobileWebElement], int],
) -> MobileWebElement | None:
  if len(elems) <= 0:
    return None

  if len(elems) == 1:
    return elems[0]

  print(f"Selecting the best matching element based from {len(elems)} elements...")

  elems_with_score = []
  for el in elems:
    score = get_match_score(el)
    elems_with_score.append((el, score))
    print(f"Element: {el.text}, Score: {score}")

  elems_with_score.sort(key=lambda x: x[1], reverse=True)
  return elems_with_score[0][0]


def _cal_match_score(
  matched_text: str,
  pattern_str: str,
  regex: bool,
) -> int:
  if not matched_text:
    return 0

  def strip_wildcards_and_flags(regex: str) -> str:
    if not regex:
      return regex

    regex = re.sub(r"\(\?[a-zA-Z]+\)", "", regex)
    regex = regex.replace(".*", "")
    return regex.strip()

  matched_text = matched_text.strip()
  pattern_str = pattern_str.strip()
  pattern_str = strip_wildcards_and_flags(pattern_str) if regex else pattern_str

  matched = len(pattern_str) / len(matched_text)
  matched = int(100 * matched)
  return matched


class Faker:

  def generate_alphanumeric(self, length: int = 8) -> str:
    return ''.join(choice(string.ascii_letters + string.digits) for _ in range(length))

  def generate_numeric(self, length: int = 8) -> str:
    return ''.join(choice(string.digits) for _ in range(length))

  def generate_char(self, length: int = 8) -> str:
    return ''.join(choice(string.ascii_letters) for _ in range(length))
