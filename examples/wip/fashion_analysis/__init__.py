"""
Fashion Analysis Pipeline Package

A comprehensive AI pipeline for analyzing fashion photos, generating creative variations,
and synthesizing new images with modified garment details.
"""

from .fashion_concepts import (
    FashionPhoto,
    GarmentAnalysis,
    DetailVariation,
    ImagePrompt,
    FashionReport,
    GeneratedImage,
    GarmentDetail,
    MarketAssessment,
    TechnicalConsiderations,
)

__all__ = [
    "FashionPhoto",
    "GarmentAnalysis", 
    "DetailVariation",
    "ImagePrompt",
    "FashionReport",
    "GeneratedImage",
    "GarmentDetail",
    "MarketAssessment",
    "TechnicalConsiderations",
]

__version__ = "1.0.0"
__author__ = "Pipelex Cookbook"
__description__ = "AI-powered fashion analysis and variation generation pipeline"