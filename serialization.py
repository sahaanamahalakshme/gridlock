"""Utility to clean numpy types for JSON serialization."""

import numpy as np


def clean_numpy(obj):

    if isinstance(obj, dict):

        return {k: clean_numpy(v) for k, v in obj.items()}

    if isinstance(obj, list):

        return [clean_numpy(v) for v in obj]

    if isinstance(obj, np.floating):

        return float(obj)

    if isinstance(obj, np.integer):

        return int(obj)

    if isinstance(obj, np.bool_):

        return bool(obj)

    if isinstance(obj, np.ndarray):

        return obj.tolist()

    return obj
