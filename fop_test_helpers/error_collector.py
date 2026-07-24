"""
Global error collector for pytest mode
"""

class ErrorCollector:
    """Collect errors during pytest execution"""
    _errors = []
    _test_count = 0
    _passed_count = 0
    _failed_count = 0
    
    @classmethod
    def reset(cls):
        cls._errors = []
        cls._test_count = 0
        cls._passed_count = 0
        cls._failed_count = 0
    
    @classmethod
    def add_error(cls, error):
        cls._errors.append(error)
        cls._failed_count += 1
    
    @classmethod
    def add_passed(cls):
        cls._passed_count += 1
    
    @classmethod
    def increment_total(cls):
        cls._test_count += 1
    
    @classmethod
    def get_errors(cls):
        return cls._errors
    
    @classmethod
    def get_summary(cls):
        return {
            'total': cls._test_count,
            'passed': cls._passed_count,
            'failed': cls._failed_count,
            'error_count': len(cls._errors)
        }