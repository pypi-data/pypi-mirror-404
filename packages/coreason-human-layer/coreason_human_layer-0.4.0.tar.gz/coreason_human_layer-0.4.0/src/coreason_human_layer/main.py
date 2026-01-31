# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_human_layer

from coreason_human_layer.utils.logger import logger


def hello_world() -> str:
    """Simple hello world function for verification.

    Returns:
        The string 'Hello World!'.
    """
    logger.info("Hello World!")
    return "Hello World!"
