import re
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PySide6.QtCore import QRegularExpression
from app.ui.theme import DesignTokens

class YAMLHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for YAML, Dockerfile, HCL, and JSON files."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Key format (blue)
        key_format = QTextCharFormat()
        key_format.setForeground(QColor(DesignTokens.ACCENT_BLUE))
        key_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r"^[\s\-]*[a-zA-Z0-9_\-\.]+:(?=\s|$)"), key_format))
        self.highlighting_rules.append((QRegularExpression(r'"[a-zA-Z0-9_\-\.]+"\s*:'), key_format))

        # String format (green)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(DesignTokens.ACCENT_GREEN))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*?'"), string_format))

        # Comment format (muted grey)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(DesignTokens.TEXT_MUTED))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r"#.*$"), comment_format))

        # Keyword / Variable format (purple)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(DesignTokens.ACCENT_PURPLE))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ["name", "on", "jobs", "steps", "uses", "run", "with", "env", "FROM", "RUN", "CMD", "EXPOSE", "COPY", "WORKDIR", "resource", "variable", "output"]
        for kw in keywords:
            pattern = QRegularExpression(rf"\b{kw}\b")
            self.highlighting_rules.append((pattern, keyword_format))

    def highlightBlock(self, text: str):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
