"""Custom themes for Conviertlo"""
from textual.theme import Theme

CONVIERTLO_DARK = Theme(
    name="conviertlo-dark",
    primary="#FFD84D",
    secondary="#FFB347",
    accent="#FFE27A",
    success="#35D07F",
    warning="#FFB347",
    error="#FF4D4F",
    background="#14161A",
    surface="#1B1F26",
    panel="#232833",
    foreground="#E8ECF1",
    dark=True,
    variables={
        "block-cursor-foreground": "#14161A",
        "block-cursor-background": "#FFD84D",
        "input-selection-background": "#FFD84D 40%",
        "footer-key-foreground": "#FFD84D",
        "border": "#FFD84D",
    }
)

# Register in app.py:
# self.register_theme(CONVIERTLO_DARK)
# self.theme = "conviertlo-dark"