#! /usr/local/bin/python3
"""Mixin class providing list handling for MultiFormat."""

# Copyright (c) 2025 - 2026 Tom Björkholm
# MIT License
#

from enum import IntEnum, auto
from typing import TypedDict, Optional, Protocol
from mformat.mformat_state import MultiFormatState, FormattingWithWS, \
    Formatting


class PointListType(IntEnum):
    """Enum for the type of point list."""

    BULLET = auto()
    NUMBERED = auto()


POINT_LIST_TYPE_NAMES = {
    PointListType.BULLET: 'bullet',
    PointListType.NUMBERED: 'numbered'
}
POINT_LIST_TYPE_STATES = {
    PointListType.BULLET: (MultiFormatState.BULLET_LIST,
                           MultiFormatState.BULLET_LIST_ITEM),
    PointListType.NUMBERED: (MultiFormatState.NUMBERED_LIST,
                             MultiFormatState.NUMBERED_LIST_ITEM)
}
LIST_STATES = (MultiFormatState.BULLET_LIST,
               MultiFormatState.BULLET_LIST_ITEM,
               MultiFormatState.NUMBERED_LIST,
               MultiFormatState.NUMBERED_LIST_ITEM)
LIST_ITEM_STATES = (MultiFormatState.BULLET_LIST_ITEM,
                    MultiFormatState.NUMBERED_LIST_ITEM)


class LevelFunc(Protocol):  # pylint: disable=too-few-public-methods
    """Function that takes a level and returns None."""

    def __call__(self, level: int) -> None: ...  # noqa: D102


class PointStackItem(TypedDict):
    """Item in the point list stack."""

    point_list_type: PointListType
    number_at_level: int


class ListHandlerMixin:  # pylint: disable=too-few-public-methods
    """Mixin providing list handling functionality for MultiFormat.

    This mixin provides the implementation of the handling of bullet
    and numbered lists. It accesses state variables (point_list_stack,
    state, etc.) through self. The derived class must implement the
    abstract methods, and MultiFormat must provide the start state
    for self.state and the public methods start_bullet_item,
    start_numbered_item.

    The mixin defines:
    - Internal state machine: _start_list_item_impl and helpers
    - Abstract methods for derived classes to implement
    """

    def __init__(self) -> None:
        """Initialize the ListHandlerMixin."""
        self.state: MultiFormatState = MultiFormatState.EMPTY
        self.point_list_stack: list[PointStackItem] = []
        self.ws_needed_at_append: bool = False
        self._start_list_dispatcher: \
            dict[PointListType, LevelFunc] = {
                PointListType.BULLET: self._start_bullet_list,
                PointListType.NUMBERED: self._start_numbered_list,
            }
        self._end_list_dispatcher: \
            dict[PointListType, LevelFunc] = {
                PointListType.BULLET: self._end_bullet_list,
                PointListType.NUMBERED: self._end_numbered_list,
            }

    # =========================================================================
    # List state machine implementation
    # =========================================================================

    def _start_list_item_impl(self, text: str, level: Optional[int],
                              formatting: FormattingWithWS,
                              point_list_type: PointListType) -> None:
        """Start a list item of any type.

        Handle the full state machine for list items with a clear,
        linear flow:
        1. Calculate the effective target level
        2. Validate the level
        3. Exit any non-list state
        4. Adjust to the target level and type
        5. Start the new item
        6. Write the text

        Args:
            text: The text to write in the list item.
            level: The level of the list item (None = current or 1).
            formatting: The formatting of the text.
            point_list_type: The type of point list (bullet or numbered).
        """
        target_level = level if level else (len(self.point_list_stack) or 1)
        self._validate_list_level(target_level, point_list_type)
        if not self._is_in_list_state():
            self._end_state()
        self._adjust_to_list_level(target_level, point_list_type)
        self._start_item_in_list(point_list_type)
        self.ws_needed_at_append = False
        to_write = self._to_write(text, formatting.smart_ws, False)
        self._write_text(to_write, self.state, formatting.formatting)

    def _validate_list_level(self, target_level: int,
                             point_list_type: PointListType) -> None:
        """Validate that the target level is reachable.

        Args:
            target_level: The level to validate.
            point_list_type: The type of list (for error message).
        Raises:
            RuntimeError: If the target level skips a level.
        """
        if target_level > len(self.point_list_stack) + 1:
            type_name = self._get_point_list_type_name(point_list_type)
            raise RuntimeError(
                f'start_{type_name}_item called with level={target_level}, '
                f'but level {target_level-1} does not exist.')

    def _adjust_to_list_level(
            self, target_level: int,
            point_list_type: PointListType) -> None:
        """Adjust the list stack to the target level with the right type.

        This method handles three operations in sequence:
        1. Decrease depth: End lists until at or below target level
        2. Switch type: End list at target level if type doesn't match
        3. Increase depth: Start new list at target level if needed

        Args:
            target_level: The level to reach.
            point_list_type: The type of list needed at target level.
        """
        self._decrease_list_depth(target_level)
        self._end_wrong_list_type_at_lev(target_level, point_list_type)
        self._increase_list_depth(target_level, point_list_type)

    def _end_item_before_nesting(self) -> None:
        """End the current item before starting a nested list.

        Transitions from item state to list state. Does nothing if not
        currently in an item state or if no list exists.
        """
        if not self.point_list_stack or not self._is_in_list_item_state():
            return
        current_type = self.point_list_stack[-1]['point_list_type']
        list_state, _ = self._get_states_of_pltype(current_type)
        self._dispatch_end_item(len(self.point_list_stack), current_type)
        self.state = list_state

    def _push_and_start_list(self, point_list_type: PointListType) -> None:
        """Push a new list onto the stack and start it.

        Args:
            point_list_type: The type of list to start.
        """
        stack_item = PointStackItem(
            point_list_type=point_list_type,
            number_at_level=0)
        self.point_list_stack.append(stack_item)
        list_state, _ = self._get_states_of_pltype(point_list_type)
        self.state = list_state
        self._dispatch_start_list(len(self.point_list_stack), point_list_type)

    def _start_item_in_list(self, point_list_type: PointListType) -> None:
        """Start a new item in the current list.

        Ends the current item if in item state, then starts a new one.

        Args:
            point_list_type: The type of list item to start.
        """
        _, item_state = self._get_states_of_pltype(point_list_type)
        lev = len(self.point_list_stack)
        if self.state == item_state:
            self._dispatch_end_item(lev, point_list_type)
        self.point_list_stack[-1]['number_at_level'] += 1
        self._dispatch_start_item(lev, point_list_type)
        self.state = item_state

    def _full_number_of_list_item(self, num: int) -> str:
        """Get the full number of the current item."""
        full_number = ''
        assert isinstance(num, int)
        assert self.point_list_stack
        assert self.point_list_stack[-1]['number_at_level'] == num
        for stack_item in self.point_list_stack:
            full_number += f'{stack_item["number_at_level"]}.'
        return full_number

    def _decrease_list_depth(self, target_level: int) -> None:
        """Decrease depth: End lists until at or below target level."""
        while len(self.point_list_stack) > target_level:
            self._end_list_state()

    def _end_wrong_list_type_at_lev(self, target_level: int,
                                    point_list_type: PointListType) -> None:
        """End list at target level if type doesn't match."""
        if len(self.point_list_stack) == target_level:
            if self.point_list_stack[-1]['point_list_type'] != point_list_type:
                self._end_list_state()

    def _increase_list_depth(self, target_level: int,
                             point_list_type: PointListType) -> None:
        """Increase depth: Start new list at target level if needed."""
        if len(self.point_list_stack) < target_level:
            self._end_item_before_nesting()
            self._push_and_start_list(point_list_type)
        # Previously we checked that max one level was missing
        assert len(self.point_list_stack) == target_level

    # =========================================================================
    # Helper methods for list type handling
    # =========================================================================

    @staticmethod
    def _get_states_of_pltype(point_list_type: PointListType) -> \
            tuple[MultiFormatState, MultiFormatState]:
        """Get the list and item states for a point list type.

        Args:
            point_list_type: The type of point list.
        Returns:
            A tuple of (list_state, item_state).
        """
        return POINT_LIST_TYPE_STATES[point_list_type]

    @staticmethod
    def _get_point_list_type_name(point_list_type: PointListType) -> str:
        """Get the name of a point list type for error messages."""
        return POINT_LIST_TYPE_NAMES[point_list_type]

    def _is_in_list_state(self) -> bool:
        """Check if currently in any list state (list or item)."""
        return self.state in LIST_STATES

    def _is_in_list_item_state(self) -> bool:
        """Check if currently in any list item state."""
        return self.state in LIST_ITEM_STATES

    # =========================================================================
    # Dispatch methods - call the appropriate derived class method
    # =========================================================================

    def _dispatch_start_list(self, level: int,
                             point_list_type: PointListType) -> None:
        """Call the appropriate _start_*_list method."""
        self._start_list_dispatcher[point_list_type](level=level)

    def _dispatch_end_list(self, level: int,
                           point_list_type: PointListType) -> None:
        """Call the appropriate _end_*_list method."""
        self._end_list_dispatcher[point_list_type](level=level)

    def _dispatch_start_item(self, level: int,
                             point_list_type: PointListType) -> None:
        """Call the appropriate _start_*_item method."""
        if point_list_type == PointListType.BULLET:
            self._start_bullet_item(level=level)
        else:
            num = self.point_list_stack[-1]['number_at_level']
            full_number = self._full_number_of_list_item(num=num)
            self._start_numbered_item(level=level, num=num,
                                      full_number=full_number)

    def _dispatch_end_item(self, level: int,
                           point_list_type: PointListType) -> None:
        """Call the appropriate _end_*_item method."""
        if point_list_type == PointListType.BULLET:
            self._end_bullet_item(level=level)
        else:
            num = self.point_list_stack[-1]['number_at_level']
            self._end_numbered_item(level=level, num=num)

    # =========================================================================
    # State management helpers
    # =========================================================================

    def _state_from_point_list(self) -> None:
        """Set the state from the point list stack."""
        if not self.point_list_stack:
            self.state = MultiFormatState.PARAGRAPH_END
            return
        point_list_type = self.point_list_stack[-1]['point_list_type']
        list_state, _ = self._get_states_of_pltype(point_list_type)
        self.state = list_state

    def _end_list_state(self) -> None:
        """End a list state."""
        assert self.point_list_stack
        assert self._is_in_list_state()
        point_list_type = self.point_list_stack[-1]['point_list_type']
        list_state, item_state = self._get_states_of_pltype(point_list_type)
        lev = len(self.point_list_stack)
        if self.state == item_state:
            self._dispatch_end_item(level=lev, point_list_type=point_list_type)
            self.state = list_state
        if self.state == list_state:
            self._dispatch_end_list(level=lev, point_list_type=point_list_type)
            self.point_list_stack.pop()
            self._state_from_point_list()

    # =========================================================================
    # Abstract methods - must be implemented by MultiFormat
    # =========================================================================

    def _end_state(self) -> None:
        """End the current state."""
        raise NotImplementedError('_end_state must be overridden')

    def _to_write(self, text: str, smart_ws: bool, in_add: bool) -> str:
        """Get the text to write."""
        raise NotImplementedError('_to_write must be overridden')

    def _write_text(self, text: str, state: MultiFormatState,
                    formatting: Formatting) -> None:
        """Write the text."""
        raise NotImplementedError('_write_text must be overridden')

    # =========================================================================
    # Abstract methods - must be implemented by derived classes
    # =========================================================================

    def _start_bullet_list(self, level: int) -> None:
        """Start a bullet list. Must be overridden by subclasses."""
        raise NotImplementedError('_start_bullet_list must be overridden')

    def _end_bullet_list(self, level: int) -> None:
        """End a bullet list. Must be overridden by subclasses."""
        raise NotImplementedError('_end_bullet_list must be overridden')

    def _start_bullet_item(self, level: int) -> None:
        """Start a bullet item. Must be overridden by subclasses."""
        raise NotImplementedError('_start_bullet_item must be overridden')

    def _end_bullet_item(self, level: int) -> None:
        """End a bullet item. Must be overridden by subclasses."""
        raise NotImplementedError('_end_bullet_item must be overridden')

    def _start_numbered_list(self, level: int) -> None:
        """Start a numbered list. Must be overridden by subclasses."""
        raise NotImplementedError('_start_numbered_list must be overridden')

    def _end_numbered_list(self, level: int) -> None:
        """End a numbered list. Must be overridden by subclasses."""
        raise NotImplementedError('_end_numbered_list must be overridden')

    def _start_numbered_item(self, level: int, num: int,
                             full_number: str) -> None:
        """Start a numbered item. Must be overridden by subclasses."""
        raise NotImplementedError('_start_numbered_item must be overridden')

    def _end_numbered_item(self, level: int, num: int) -> None:
        """End a numbered item. Must be overridden by subclasses."""
        raise NotImplementedError('_end_numbered_item must be overridden')
