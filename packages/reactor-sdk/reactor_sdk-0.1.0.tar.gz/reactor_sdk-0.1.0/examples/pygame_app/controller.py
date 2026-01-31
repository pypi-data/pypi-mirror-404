"""
ReactorController - Dynamic UI controller for pygame.

This module provides a controller that dynamically builds UI controls
based on the model's capabilities schema, similar to ReactorController.tsx.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import pygame

from reactor_sdk import Reactor, ReactorStatus
from reactor_sdk.types import (
    CapabilitiesMessage,
    CommandSchema,
    ParameterSchema,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Colors
# =============================================================================

COLORS = {
    "background": (250, 250, 250),
    "panel": (255, 255, 255),
    "border": (221, 221, 221),
    "text": (51, 51, 51),
    "text_light": (102, 102, 102),
    "text_muted": (136, 136, 136),
    "primary": (0, 123, 255),
    "primary_hover": (0, 105, 217),
    "slider_track": (200, 200, 200),
    "slider_fill": (0, 123, 255),
    "slider_thumb": (255, 255, 255),
    "checkbox_checked": (0, 123, 255),
    "input_bg": (255, 255, 255),
    "input_border": (204, 204, 204),
    "required": (255, 0, 0),
    "header_bg": (240, 240, 240),
    "expand_arrow": (153, 153, 153),
}


# =============================================================================
# UI Element Classes
# =============================================================================


@dataclass
class UIElement:
    """Base class for UI elements."""

    rect: pygame.Rect
    param_name: str
    param_schema: ParameterSchema
    value: Any = None


@dataclass
class SliderElement(UIElement):
    """Slider UI element for number/integer with min/max."""

    min_value: float = 0.0
    max_value: float = 1.0
    is_integer: bool = False
    dragging: bool = False


@dataclass
class TextInputElement(UIElement):
    """Text input UI element."""

    text: str = ""
    focused: bool = False
    cursor_pos: int = 0


@dataclass
class CheckboxElement(UIElement):
    """Checkbox UI element for boolean."""

    checked: bool = False


@dataclass
class DropdownElement(UIElement):
    """Dropdown UI element for string with enum."""

    options: list[str] = field(default_factory=list)
    selected_index: int = 0
    expanded: bool = False


@dataclass
class CommandUI:
    """UI state for a command."""

    name: str
    schema: CommandSchema
    elements: list[UIElement] = field(default_factory=list)
    expanded: bool = False
    rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    header_rect: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
    button_rect: Optional[pygame.Rect] = None


# =============================================================================
# ReactorController
# =============================================================================


class ReactorController:
    """
    Dynamic UI controller that builds controls from model capabilities.

    Similar to ReactorController.tsx, this class:
    1. Listens for capabilities schema from the model
    2. Dynamically builds UI controls based on command schemas
    3. Sends commands when controls are changed
    """

    def __init__(
        self,
        reactor: Reactor,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> None:
        """
        Initialize the ReactorController.

        Args:
            reactor: The Reactor instance.
            x: X position of the controller panel.
            y: Y position of the controller panel.
            width: Width of the controller panel.
            height: Height of the controller panel.
        """
        self.reactor = reactor
        self.rect = pygame.Rect(x, y, width, height)
        self.commands: dict[str, CommandUI] = {}
        self.scroll_offset = 0
        self.max_scroll = 0

        # Font setup
        pygame.font.init()
        self.font = pygame.font.SysFont("monospace", 12)
        self.font_bold = pygame.font.SysFont("monospace", 12, bold=True)
        self.font_title = pygame.font.SysFont("monospace", 14, bold=True)

        # Capabilities request retry
        self._capabilities_received = False
        self._last_request_time = 0.0

        # Register event handlers using decorators
        @reactor.on_message
        def handle_message(message: Any) -> None:
            if isinstance(message, dict) and "commands" in message:
                logger.debug("Received capabilities schema")
                self._capabilities_received = True
                self._parse_capabilities(message)  # type: ignore

        @reactor.on_status(ReactorStatus.DISCONNECTED)
        def handle_disconnected(status: ReactorStatus) -> None:
            self.commands.clear()
            self._capabilities_received = False

        @reactor.on_status(ReactorStatus.READY)
        def handle_ready(status: ReactorStatus) -> None:
            self._request_capabilities()

    def _request_capabilities(self) -> None:
        """Request capabilities from the model."""
        import time

        current_time = time.time()
        if current_time - self._last_request_time < 1.0:
            return

        self._last_request_time = current_time
        logger.debug("Requesting capabilities")

        # Create task for async send
        asyncio.create_task(
            self.reactor.send_command("requestCapabilities", {})
        )

    def _parse_capabilities(self, message: CapabilitiesMessage) -> None:
        """Parse capabilities schema and create UI elements."""
        self.commands.clear()

        for command_name, command_schema in message["commands"].items():
            command_ui = CommandUI(
                name=command_name,
                schema=command_schema,
                expanded=False,
            )

            # Create UI elements for each parameter
            for param_name, param_schema in command_schema["schema"].items():
                element = self._create_element(param_name, param_schema)
                if element:
                    command_ui.elements.append(element)

            self.commands[command_name] = command_ui

        self._layout_commands()

    def _create_element(
        self,
        param_name: str,
        param_schema: ParameterSchema,
    ) -> Optional[UIElement]:
        """Create a UI element for a parameter."""
        param_type = param_schema.get("type", "string")
        dummy_rect = pygame.Rect(0, 0, 0, 0)

        if param_type in ("number", "integer"):
            min_val = param_schema.get("minimum")
            max_val = param_schema.get("maximum")

            if min_val is not None and max_val is not None:
                # Slider for bounded numbers
                return SliderElement(
                    rect=dummy_rect,
                    param_name=param_name,
                    param_schema=param_schema,
                    value=min_val,
                    min_value=float(min_val),
                    max_value=float(max_val),
                    is_integer=(param_type == "integer"),
                )
            else:
                # Text input for unbounded numbers
                return TextInputElement(
                    rect=dummy_rect,
                    param_name=param_name,
                    param_schema=param_schema,
                    value=0,
                    text="0",
                )

        elif param_type == "string":
            enum_values = param_schema.get("enum")
            if enum_values:
                # Dropdown for enum
                return DropdownElement(
                    rect=dummy_rect,
                    param_name=param_name,
                    param_schema=param_schema,
                    value=enum_values[0] if enum_values else "",
                    options=enum_values,
                )
            else:
                # Text input for strings
                return TextInputElement(
                    rect=dummy_rect,
                    param_name=param_name,
                    param_schema=param_schema,
                    value="",
                    text="",
                )

        elif param_type == "boolean":
            return CheckboxElement(
                rect=dummy_rect,
                param_name=param_name,
                param_schema=param_schema,
                value=False,
                checked=False,
            )

        return None

    def _layout_commands(self) -> None:
        """Layout all command UI elements."""
        y = self.rect.y + 50  # After title
        padding = 8
        element_height = 30

        for command_ui in self.commands.values():
            # Command header
            header_height = 40
            command_ui.header_rect = pygame.Rect(
                self.rect.x + padding,
                y - self.scroll_offset,
                self.rect.width - padding * 2,
                header_height,
            )
            command_ui.rect = pygame.Rect(
                self.rect.x + padding,
                y - self.scroll_offset,
                self.rect.width - padding * 2,
                header_height,
            )
            y += header_height

            if command_ui.expanded:
                # Layout elements
                for element in command_ui.elements:
                    element.rect = pygame.Rect(
                        self.rect.x + padding * 2,
                        y - self.scroll_offset,
                        self.rect.width - padding * 4,
                        element_height,
                    )
                    y += element_height + 4

                # Check if we need an execute button (no sliders)
                has_slider = any(
                    isinstance(e, SliderElement) for e in command_ui.elements
                )
                if not has_slider:
                    command_ui.button_rect = pygame.Rect(
                        self.rect.x + padding * 2,
                        y - self.scroll_offset,
                        100,
                        30,
                    )
                    y += 40
                else:
                    command_ui.button_rect = None

                # Update command rect to include content
                content_height = y - self.scroll_offset - command_ui.rect.y
                command_ui.rect.height = content_height

            y += padding

        # Update max scroll
        self.max_scroll = max(0, y - self.rect.y - self.rect.height)

    def render(self, surface: pygame.Surface) -> None:
        """
        Render the controller UI.

        Args:
            surface: The pygame surface to render to.
        """
        # Create clip rect for scrolling
        clip_rect = self.rect.copy()
        surface.set_clip(clip_rect)

        # Background
        pygame.draw.rect(surface, COLORS["panel"], self.rect)
        pygame.draw.rect(surface, COLORS["border"], self.rect, 1)

        # Title
        title_text = self.font_title.render("Reactor Commands", True, COLORS["text"])
        surface.blit(title_text, (self.rect.x + 12, self.rect.y + 12))

        if not self.commands:
            # Waiting message
            wait_text = self.font.render(
                "Waiting for commands schema...",
                True,
                COLORS["text_muted"],
            )
            surface.blit(wait_text, (self.rect.x + 12, self.rect.y + 50))
            surface.set_clip(None)
            return

        # Render commands
        for command_ui in self.commands.values():
            self._render_command(surface, command_ui)

        # Remove clip
        surface.set_clip(None)

    def _render_command(
        self,
        surface: pygame.Surface,
        command_ui: CommandUI,
    ) -> None:
        """Render a single command UI."""
        # Skip if completely outside visible area
        if command_ui.header_rect.bottom < self.rect.top:
            return
        if command_ui.header_rect.top > self.rect.bottom:
            return

        # Header background
        pygame.draw.rect(surface, COLORS["header_bg"], command_ui.header_rect)
        pygame.draw.rect(surface, COLORS["border"], command_ui.header_rect, 1)

        # Command name
        name_text = self.font_bold.render(command_ui.name, True, COLORS["text"])
        surface.blit(
            name_text,
            (command_ui.header_rect.x + 12, command_ui.header_rect.y + 12),
        )

        # Expand arrow
        arrow = "▼" if command_ui.expanded else "▶"
        arrow_text = self.font.render(arrow, True, COLORS["expand_arrow"])
        surface.blit(
            arrow_text,
            (
                command_ui.header_rect.right - 24,
                command_ui.header_rect.y + 12,
            ),
        )

        if not command_ui.expanded:
            return

        # Render elements
        for element in command_ui.elements:
            if element.rect.bottom < self.rect.top:
                continue
            if element.rect.top > self.rect.bottom:
                continue

            if isinstance(element, SliderElement):
                self._render_slider(surface, element)
            elif isinstance(element, TextInputElement):
                self._render_text_input(surface, element)
            elif isinstance(element, CheckboxElement):
                self._render_checkbox(surface, element)
            elif isinstance(element, DropdownElement):
                self._render_dropdown(surface, element)

        # Execute button
        if command_ui.button_rect:
            pygame.draw.rect(surface, COLORS["primary"], command_ui.button_rect)
            btn_text = self.font_bold.render("Execute", True, (255, 255, 255))
            text_rect = btn_text.get_rect(center=command_ui.button_rect.center)
            surface.blit(btn_text, text_rect)

    def _render_slider(self, surface: pygame.Surface, element: SliderElement) -> None:
        """Render a slider element."""
        # Label
        label = f"{element.param_name} ({element.min_value:.1f} - {element.max_value:.1f})"
        if element.param_schema.get("required"):
            label += " *"
        label_text = self.font.render(label, True, COLORS["text_light"])
        surface.blit(label_text, (element.rect.x, element.rect.y))

        # Track
        track_rect = pygame.Rect(
            element.rect.x,
            element.rect.y + 16,
            element.rect.width - 60,
            4,
        )
        pygame.draw.rect(surface, COLORS["slider_track"], track_rect)

        # Fill
        progress = (element.value - element.min_value) / (
            element.max_value - element.min_value
        )
        fill_width = int(track_rect.width * progress)
        fill_rect = pygame.Rect(track_rect.x, track_rect.y, fill_width, 4)
        pygame.draw.rect(surface, COLORS["slider_fill"], fill_rect)

        # Thumb
        thumb_x = track_rect.x + fill_width
        pygame.draw.circle(
            surface,
            COLORS["slider_thumb"],
            (thumb_x, track_rect.centery),
            8,
        )
        pygame.draw.circle(
            surface,
            COLORS["slider_fill"],
            (thumb_x, track_rect.centery),
            8,
            2,
        )

        # Value text
        if element.is_integer:
            value_str = f"{int(element.value)}"
        else:
            value_str = f"{element.value:.2f}"
        value_text = self.font.render(value_str, True, COLORS["text_muted"])
        surface.blit(
            value_text,
            (track_rect.right + 8, element.rect.y + 10),
        )

    def _render_text_input(
        self,
        surface: pygame.Surface,
        element: TextInputElement,
    ) -> None:
        """Render a text input element."""
        # Label
        label = element.param_name
        if element.param_schema.get("required"):
            label += " *"
        label_text = self.font.render(label, True, COLORS["text_light"])
        surface.blit(label_text, (element.rect.x, element.rect.y))

        # Input box
        input_rect = pygame.Rect(
            element.rect.x,
            element.rect.y + 14,
            element.rect.width,
            18,
        )
        pygame.draw.rect(surface, COLORS["input_bg"], input_rect)
        border_color = COLORS["primary"] if element.focused else COLORS["input_border"]
        pygame.draw.rect(surface, border_color, input_rect, 1)

        # Text
        text_surface = self.font.render(element.text, True, COLORS["text"])
        surface.blit(text_surface, (input_rect.x + 4, input_rect.y + 2))

    def _render_checkbox(
        self,
        surface: pygame.Surface,
        element: CheckboxElement,
    ) -> None:
        """Render a checkbox element."""
        # Checkbox box
        box_rect = pygame.Rect(element.rect.x, element.rect.y + 8, 14, 14)
        pygame.draw.rect(surface, COLORS["input_bg"], box_rect)
        pygame.draw.rect(surface, COLORS["input_border"], box_rect, 1)

        if element.checked:
            # Check mark
            inner_rect = pygame.Rect(
                box_rect.x + 3,
                box_rect.y + 3,
                8,
                8,
            )
            pygame.draw.rect(surface, COLORS["checkbox_checked"], inner_rect)

        # Label
        label = element.param_name
        if element.param_schema.get("required"):
            label += " *"
        label_text = self.font.render(label, True, COLORS["text_light"])
        surface.blit(label_text, (box_rect.right + 8, element.rect.y + 8))

    def _render_dropdown(
        self,
        surface: pygame.Surface,
        element: DropdownElement,
    ) -> None:
        """Render a dropdown element."""
        # Label
        label = element.param_name
        if element.param_schema.get("required"):
            label += " *"
        label_text = self.font.render(label, True, COLORS["text_light"])
        surface.blit(label_text, (element.rect.x, element.rect.y))

        # Dropdown box
        dropdown_rect = pygame.Rect(
            element.rect.x,
            element.rect.y + 14,
            element.rect.width,
            18,
        )
        pygame.draw.rect(surface, COLORS["input_bg"], dropdown_rect)
        pygame.draw.rect(surface, COLORS["input_border"], dropdown_rect, 1)

        # Selected value
        selected_value = (
            element.options[element.selected_index]
            if element.options
            else "Select..."
        )
        text_surface = self.font.render(selected_value, True, COLORS["text"])
        surface.blit(text_surface, (dropdown_rect.x + 4, dropdown_rect.y + 2))

        # Arrow
        arrow_text = self.font.render("▼", True, COLORS["text_muted"])
        surface.blit(arrow_text, (dropdown_rect.right - 16, dropdown_rect.y + 2))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events.

        Args:
            event: The pygame event.

        Returns:
            True if the event was handled.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self._handle_click(event.pos)
            elif event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 20)
                self._layout_commands()
                return True
            elif event.button == 5:  # Scroll down
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 20)
                self._layout_commands()
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._handle_mouse_up()

        elif event.type == pygame.MOUSEMOTION:
            return self._handle_mouse_motion(event.pos)

        elif event.type == pygame.KEYDOWN:
            return self._handle_key(event)

        return False

    def _handle_click(self, pos: tuple[int, int]) -> bool:
        """Handle mouse click."""
        if not self.rect.collidepoint(pos):
            return False

        for command_ui in self.commands.values():
            # Check header click (expand/collapse)
            if command_ui.header_rect.collidepoint(pos):
                command_ui.expanded = not command_ui.expanded
                self._layout_commands()
                return True

            # Check button click
            if command_ui.button_rect and command_ui.button_rect.collidepoint(pos):
                self._execute_command(command_ui)
                return True

            # Check element clicks
            if command_ui.expanded:
                for element in command_ui.elements:
                    if self._handle_element_click(element, pos, command_ui):
                        return True

        return False

    def _handle_element_click(
        self,
        element: UIElement,
        pos: tuple[int, int],
        command_ui: CommandUI,
    ) -> bool:
        """Handle click on an element."""
        if not element.rect.collidepoint(pos):
            return False

        if isinstance(element, SliderElement):
            element.dragging = True
            self._update_slider_value(element, pos[0])
            self._execute_command(command_ui)
            return True

        elif isinstance(element, CheckboxElement):
            element.checked = not element.checked
            element.value = element.checked
            return True

        elif isinstance(element, TextInputElement):
            # Unfocus other inputs
            for cmd in self.commands.values():
                for el in cmd.elements:
                    if isinstance(el, TextInputElement):
                        el.focused = False
            element.focused = True
            return True

        elif isinstance(element, DropdownElement):
            # Cycle through options
            if element.options:
                element.selected_index = (element.selected_index + 1) % len(
                    element.options
                )
                element.value = element.options[element.selected_index]
            return True

        return False

    def _handle_mouse_up(self) -> None:
        """Handle mouse button release."""
        for command_ui in self.commands.values():
            for element in command_ui.elements:
                if isinstance(element, SliderElement):
                    element.dragging = False

    def _handle_mouse_motion(self, pos: tuple[int, int]) -> bool:
        """Handle mouse motion."""
        for command_ui in self.commands.values():
            for element in command_ui.elements:
                if isinstance(element, SliderElement) and element.dragging:
                    self._update_slider_value(element, pos[0])
                    self._execute_command(command_ui)
                    return True
        return False

    def _update_slider_value(self, element: SliderElement, mouse_x: int) -> None:
        """Update slider value based on mouse position."""
        track_start = element.rect.x
        track_end = element.rect.x + element.rect.width - 60

        progress = (mouse_x - track_start) / (track_end - track_start)
        progress = max(0.0, min(1.0, progress))

        value = element.min_value + progress * (element.max_value - element.min_value)

        if element.is_integer:
            value = round(value)

        element.value = value

    def _handle_key(self, event: pygame.event.Event) -> bool:
        """Handle key press."""
        for command_ui in self.commands.values():
            for element in command_ui.elements:
                if isinstance(element, TextInputElement) and element.focused:
                    if event.key == pygame.K_BACKSPACE:
                        element.text = element.text[:-1]
                    elif event.key == pygame.K_RETURN:
                        element.focused = False
                        # Parse value
                        try:
                            if element.param_schema.get("type") in (
                                "number",
                                "integer",
                            ):
                                element.value = float(element.text)
                            else:
                                element.value = element.text
                        except ValueError:
                            element.value = element.text
                    elif event.unicode and event.unicode.isprintable():
                        element.text += event.unicode
                    return True
        return False

    def _execute_command(self, command_ui: CommandUI) -> None:
        """Execute a command with current parameter values."""
        data: dict[str, Any] = {}

        for element in command_ui.elements:
            param_name = element.param_name
            param_schema = element.param_schema
            value = element.value

            # Type conversion
            if param_schema.get("type") == "integer" and value is not None:
                value = int(value)
            elif param_schema.get("type") == "number" and value is not None:
                value = float(value)
            elif param_schema.get("type") == "boolean":
                value = bool(value)

            if value is not None and value != "":
                data[param_name] = value
            elif param_schema.get("required"):
                # Set defaults for required params
                if param_schema.get("type") in ("number", "integer"):
                    data[param_name] = param_schema.get("minimum", 0)
                elif param_schema.get("type") == "string":
                    data[param_name] = ""
                elif param_schema.get("type") == "boolean":
                    data[param_name] = False

        logger.debug(f"Executing command: {command_ui.name} with data: {data}")
        asyncio.create_task(self.reactor.send_command(command_ui.name, data))

    def update(self) -> None:
        """
        Update the controller state.

        Call this periodically to handle capabilities retry.
        """
        if (
            self.reactor.get_status() == ReactorStatus.READY
            and not self._capabilities_received
        ):
            import time

            current_time = time.time()
            if current_time - self._last_request_time >= 5.0:
                self._request_capabilities()
