from app.ui.theme import theme_manager

# Backward compatibility bindings for legacy imports
DARK_THEME_QSS = theme_manager.get_stylesheet("Dark")
LIGHT_THEME_QSS = theme_manager.get_stylesheet("Light")
