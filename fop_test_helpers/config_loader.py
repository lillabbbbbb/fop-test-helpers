# lib/config_loader.py
"""
Load test configurations from JSON files
"""
import json
import os

def load_config_from_dict(config_dict):
    """Use configuration from dictionary"""
    return config_dict


def get_function_names(config):
    """Get list of function names from config"""
    return list(config.keys())


def get_test_cases(config, function_name):
    """Get test cases for a specific function"""
    return config.get(function_name, {}).get("runtime", {}).get("cases", [])