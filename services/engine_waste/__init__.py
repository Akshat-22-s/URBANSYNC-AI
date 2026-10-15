"""Waste management engine module for UrbanSync AI."""

from .cvrp_solver import solve_cvrp
from .change_detector import detect_debris_change
from .fill_model import predict_fill_rate

__all__ = [
    "solve_cvrp",
    "detect_debris_change",
    "predict_fill_rate",
]
