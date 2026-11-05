import pygame


def fit_viewport(logical_size, window_size):
    """Return a centered viewport that preserves the logical aspect ratio."""
    logical_width, logical_height = logical_size
    window_width, window_height = window_size
    scale = min(window_width / logical_width, window_height / logical_height)
    width = max(1, round(logical_width * scale))
    height = max(1, round(logical_height * scale))
    return pygame.Rect(
        (window_width - width) // 2,
        (window_height - height) // 2,
        width,
        height,
    )


def window_to_logical(position, viewport, logical_size):
    """Map a window-space mouse position into logical simulation coordinates."""
    logical_width, logical_height = logical_size
    return (
        (position[0] - viewport.left) * logical_width / viewport.width,
        (position[1] - viewport.top) * logical_height / viewport.height,
    )
