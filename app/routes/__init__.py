# so that 'from app.routes import cars_bp' works
from .cars    import cars_bp
from .rentals import rentals_bp


__all__ = ["cars_bp", "rentals_bp"]
