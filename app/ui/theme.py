from typing import Dict, Any

class DesignTokens:
    """Enterprise UI Design Tokens and Color Palette Constants."""
    # Dark Mode Palette
    DARK_BG_MAIN = "#0D1117"
    DARK_BG_SURFACE = "#161B22"
    DARK_BG_CARD = "#21262D"
    DARK_BORDER = "#30363D"

    # Brand & Accent Colors
    ACCENT_BLUE = "#58A6FF"
    ACCENT_GREEN = "#3FB950"
    ACCENT_AMBER = "#D29922"
    ACCENT_RED = "#F85149"
    ACCENT_PURPLE = "#A371F7"

    # Typography Colors
    TEXT_PRIMARY = "#F0F6FC"
    TEXT_SECONDARY = "#8B949E"
    TEXT_MUTED = "#484F58"

class ThemeManager:
    """App-wide stylesheet and theme management engine."""

    @staticmethod
    def get_dark_stylesheet() -> str:
        """Return enterprise dark mode Qt Style Sheet (QSS)."""
        return f"""
        QMainWindow, QDialog {{
            background-color: {DesignTokens.DARK_BG_MAIN};
            color: {DesignTokens.TEXT_PRIMARY};
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            font-size: 13px;
        }}

        QWidget {{
            background-color: {DesignTokens.DARK_BG_MAIN};
            color: {DesignTokens.TEXT_PRIMARY};
        }}

        QGroupBox, QFrame.card {{
            background-color: {DesignTokens.DARK_BG_SURFACE};
            border: 1px solid {DesignTokens.DARK_BORDER};
            border-radius: 8px;
            margin-top: 8px;
            padding: 12px;
        }}

        QLabel {{
            background: transparent;
            color: {DesignTokens.TEXT_PRIMARY};
        }}

        QLabel.secondary {{
            color: {DesignTokens.TEXT_SECONDARY};
            font-size: 12px;
        }}

        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
            background-color: {DesignTokens.DARK_BG_CARD};
            border: 1px solid {DesignTokens.DARK_BORDER};
            border-radius: 6px;
            color: {DesignTokens.TEXT_PRIMARY};
            padding: 8px;
            selection-background-color: {DesignTokens.ACCENT_BLUE};
        }}

        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
            border: 1px solid {DesignTokens.ACCENT_BLUE};
        }}

        QPushButton {{
            background-color: {DesignTokens.DARK_BG_CARD};
            border: 1px solid {DesignTokens.DARK_BORDER};
            border-radius: 6px;
            color: {DesignTokens.TEXT_PRIMARY};
            padding: 8px 16px;
            font-weight: 600;
        }}

        QPushButton:hover {{
            background-color: {DesignTokens.DARK_BORDER};
            border-color: {DesignTokens.ACCENT_BLUE};
        }}

        QPushButton:pressed {{
            background-color: {DesignTokens.DARK_BG_SURFACE};
        }}

        QPushButton.primary {{
            background-color: {DesignTokens.ACCENT_BLUE};
            color: #040D21;
            border: none;
        }}

        QPushButton.primary:hover {{
            background-color: #79B8FF;
        }}

        QPushButton.success {{
            background-color: {DesignTokens.ACCENT_GREEN};
            color: #04210B;
            border: none;
        }}

        QPushButton.danger {{
            background-color: {DesignTokens.ACCENT_RED};
            color: #FFFFFF;
            border: none;
        }}

        QTabWidget::pane {{
            border: 1px solid {DesignTokens.DARK_BORDER};
            background-color: {DesignTokens.DARK_BG_SURFACE};
            border-radius: 8px;
        }}

        QTabBar::tab {{
            background-color: {DesignTokens.DARK_BG_MAIN};
            color: {DesignTokens.TEXT_SECONDARY};
            padding: 10px 20px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            margin-right: 4px;
        }}

        QTabBar::tab:selected {{
            background-color: {DesignTokens.DARK_BG_SURFACE};
            color: {DesignTokens.ACCENT_BLUE};
            border-bottom: 2px solid {DesignTokens.ACCENT_BLUE};
            font-weight: bold;
        }}

        QProgressBar {{
            border: 1px solid {DesignTokens.DARK_BORDER};
            border-radius: 4px;
            text-align: center;
            background-color: {DesignTokens.DARK_BG_CARD};
            color: {DesignTokens.TEXT_PRIMARY};
        }}

        QProgressBar::chunk {{
            background-color: {DesignTokens.ACCENT_BLUE};
            border-radius: 3px;
        }}

        QStatusBar {{
            background-color: {DesignTokens.DARK_BG_SURFACE};
            border-top: 1px solid {DesignTokens.DARK_BORDER};
            color: {DesignTokens.TEXT_SECONDARY};
        }}

        QTableWidget, QTreeWidget {{
            background-color: {DesignTokens.DARK_BG_SURFACE};
            gridline-color: {DesignTokens.DARK_BORDER};
            border: 1px solid {DesignTokens.DARK_BORDER};
            border-radius: 6px;
        }}

        QHeaderView::section {{
            background-color: {DesignTokens.DARK_BG_CARD};
            color: {DesignTokens.TEXT_PRIMARY};
            padding: 6px;
            border: 1px solid {DesignTokens.DARK_BORDER};
            font-weight: bold;
        }}

        QWidget#SidebarWidget {{
            background-color: #0B0E14;
            border-right: 1px solid {DesignTokens.DARK_BORDER};
        }}

        QPushButton#SidebarButton {{
            text-align: left;
            background-color: transparent;
            border: none;
            border-radius: 8px;
            color: {DesignTokens.TEXT_SECONDARY};
            padding: 10px 18px;
            margin: 2px 8px;
            font-weight: 500;
        }}

        QPushButton#SidebarButton:hover {{
            background-color: {DesignTokens.DARK_BG_SURFACE};
            color: {DesignTokens.TEXT_PRIMARY};
        }}

        QPushButton#SidebarButton[active="true"] {{
            background-color: {DesignTokens.DARK_BG_CARD};
            color: {DesignTokens.ACCENT_BLUE};
            border-left: 3px solid {DesignTokens.ACCENT_BLUE};
            border-top-left-radius: 0px;
            border-bottom-left-radius: 0px;
            font-weight: bold;
        }}
        """

    @classmethod
    def get_stylesheet(cls, theme_name: str = "Dark") -> str:
        """Return stylesheet matching current theme setting."""
        return cls.get_dark_stylesheet()

# Global theme manager instance
theme_manager = ThemeManager()
