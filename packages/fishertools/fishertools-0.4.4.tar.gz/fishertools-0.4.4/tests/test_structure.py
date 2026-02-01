"""
Tests for project structure and imports.
"""

import pytest


class TestProjectStructure:
    """Tests to verify the new project structure works correctly."""
    
    def test_main_imports(self):
        """Test that main fishertools imports work."""
        import fishertools
        
        # Test that main API is available
        assert hasattr(fishertools, 'explain_error')
        
        # Test that modules are available
        assert hasattr(fishertools, 'errors')
        assert hasattr(fishertools, 'safe')
        assert hasattr(fishertools, 'learn')
        assert hasattr(fishertools, 'legacy')
    
    def test_errors_module_imports(self):
        """Test that errors module imports work."""
        from fishertools.errors import ErrorExplainer, explain_error, ErrorPattern
        from fishertools.errors.models import ErrorExplanation, ExplainerConfig
        
        # Test that classes can be instantiated
        explainer = ErrorExplainer()
        assert explainer is not None
        
        config = ExplainerConfig()
        assert config is not None
    
    def test_safe_module_imports(self):
        """Test that safe module imports work."""
        from fishertools.safe import safe_get, safe_divide, safe_read_file
        
        # Test that functions are callable
        assert callable(safe_get)
        assert callable(safe_divide)
        assert callable(safe_read_file)
    
    def test_learn_module_imports(self):
        """Test that learn module imports work."""
        from fishertools.learn import generate_example, show_best_practice
        
        # Test that functions are callable
        assert callable(generate_example)
        assert callable(show_best_practice)
    
    def test_legacy_module_imports(self):
        """Test that legacy module imports work."""
        import fishertools.legacy
        
        # Module should be importable
        assert fishertools.legacy is not None