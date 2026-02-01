"""
Property-based tests for visual documentation consistency.

Feature: fishertools-enhancements
Property 4: Visual Documentation Consistency
Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
"""

import pytest
from hypothesis import given, strategies as st, assume
from fishertools.documentation import VisualDocumentation
from fishertools.documentation.models import (
    FunctionInfo, MermaidDiagram, DiagramType, 
    FlowDiagram, Flowchart, StructureDiagram
)


# Test data generators
@st.composite
def generate_function_info(draw):
    """Generate valid FunctionInfo for testing."""
    name = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), blacklist_characters='_')))
    assume(name.isidentifier() and not name.startswith('_'))
    
    docstring = draw(st.one_of(
        st.none(),
        st.text(min_size=10, max_size=200)
    ))
    
    # Generate parameters with type annotations
    param_count = draw(st.integers(min_value=0, max_value=5))
    parameters = {}
    for i in range(param_count):
        param_name = f"param_{i}"
        param_type = draw(st.sampled_from(['str', 'int', 'float', 'bool', 'List[str]', 'Dict[str, Any]', 'Optional[str]']))
        parameters[param_name] = param_type
    
    return_type = draw(st.one_of(
        st.none(),
        st.sampled_from(['str', 'int', 'bool', 'List[str]', 'None'])
    ))
    
    return FunctionInfo(
        name=name,
        docstring=docstring,
        parameters=parameters,
        return_type=return_type,
        module_path="/fake/path/module.py",
        line_number=draw(st.integers(min_value=1, max_value=1000))
    )


@st.composite
def generate_code_sample(draw):
    """Generate valid Python code samples for testing."""
    # Generate simple but valid Python code structures
    code_templates = [
        "def {name}():\n    return {value}",
        "if {condition}:\n    print('{message}')\nelse:\n    print('alternative')",
        "for i in range({count}):\n    print(i)",
        "while {condition}:\n    {action}\n    break",
        "x = {value}\nprint(x)\nreturn x"
    ]
    
    template = draw(st.sampled_from(code_templates))
    
    # Fill in template variables
    name = draw(st.text(min_size=3, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    assume(name.isidentifier())
    
    value = draw(st.one_of(
        st.integers(min_value=1, max_value=100),
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        st.sampled_from([True, False])
    ))
    
    condition = draw(st.sampled_from(['True', 'False', 'x > 0', 'len(data) > 0']))
    message = draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    count = draw(st.integers(min_value=1, max_value=10))
    action = draw(st.sampled_from(['x += 1', 'print("loop")', 'data.append(i)']))
    
    try:
        code = template.format(
            name=name,
            value=repr(value),
            condition=condition,
            message=message,
            count=count,
            action=action
        )
        return code
    except (KeyError, ValueError):
        # If template formatting fails, return a simple default
        return f"def {name}():\n    return {repr(value)}"


@st.composite
def generate_data_structure(draw):
    """Generate various data structures for visualization testing."""
    data_type = draw(st.sampled_from(['list', 'dict', 'set', 'string', 'int', 'float', 'bool', 'none']))
    
    if data_type == 'list':
        return draw(st.lists(st.integers(min_value=0, max_value=100), max_size=15))
    elif data_type == 'dict':
        return draw(st.dictionaries(
            st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
            st.integers(min_value=0, max_value=100),
            max_size=10
        ))
    elif data_type == 'set':
        return draw(st.sets(st.integers(min_value=0, max_value=50), max_size=10))
    elif data_type == 'string':
        return draw(st.text(max_size=100))
    elif data_type == 'int':
        return draw(st.integers(min_value=-1000, max_value=1000))
    elif data_type == 'float':
        return draw(st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    elif data_type == 'bool':
        return draw(st.booleans())
    else:  # none
        return None


class TestVisualDocumentationProperties:
    """Property-based tests for visual documentation consistency."""
    
    @given(
        st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), blacklist_characters='_')), min_size=1, max_size=10),
        st.sampled_from(['modern', 'classic', 'minimal'])
    )
    def test_architecture_diagram_consistency(self, modules, style):
        """
        Property 4.1: Architecture diagram consistency
        
        For any list of modules and any style, the Visual_Documentation should 
        display architecture diagrams with consistent styling.
        
        **Validates: Requirements 4.1, 4.5**
        """
        # Filter out invalid module names
        valid_modules = [m for m in modules if m.isidentifier() and not m.startswith('_')]
        assume(len(valid_modules) > 0)
        
        visual_doc = VisualDocumentation(style=style)
        
        # Generate architecture diagram
        diagram = visual_doc.create_architecture_diagram(valid_modules)
        
        # Verify diagram structure (4.1)
        assert isinstance(diagram, MermaidDiagram)
        assert diagram.diagram_type == DiagramType.ARCHITECTURE
        assert diagram.content is not None
        assert len(diagram.content.strip()) > 0
        assert diagram.title == "Module Architecture"
        
        # Verify all modules are included in the diagram
        for module in valid_modules:
            assert module in diagram.content
        
        # Verify Mermaid syntax is valid (basic check)
        assert "graph TB" in diagram.content or "graph TD" in diagram.content
        
        # Apply consistent styling and verify consistency (4.5)
        styled_diagram = visual_doc.apply_consistent_styling(diagram)
        
        # Verify styling is applied consistently
        assert isinstance(styled_diagram, MermaidDiagram)
        assert styled_diagram.diagram_type == diagram.diagram_type
        assert styled_diagram.title == diagram.title
        
        # Verify style-specific elements are present
        if style == "modern":
            assert "#e1f5fe" in styled_diagram.content or "#01579b" in styled_diagram.content
        elif style == "classic":
            assert "#fff3e0" in styled_diagram.content or "#e65100" in styled_diagram.content
        
        # Verify theme configuration is added
        assert "%%{init:" in styled_diagram.content
    
    @given(generate_function_info(), st.sampled_from(['modern', 'classic', 'minimal']))
    def test_data_flow_diagram_consistency(self, function_info, style):
        """
        Property 4.2: Data flow diagram consistency
        
        For any function and any style, the Visual_Documentation should 
        show data flow schemes with consistent styling.
        
        **Validates: Requirements 4.2, 4.5**
        """
        visual_doc = VisualDocumentation(style=style)
        
        # Generate data flow diagram
        flow_diagram = visual_doc.generate_data_flow_diagram(function_info)
        
        # Verify diagram structure (4.2)
        assert isinstance(flow_diagram, FlowDiagram)
        assert flow_diagram.title == f"Data Flow: {function_info.name}"
        assert len(flow_diagram.nodes) >= 3  # At least input, process, output
        assert len(flow_diagram.edges) >= 2  # At least input->process, process->output
        
        # Verify required nodes are present
        node_types = [node.get('type') for node in flow_diagram.nodes]
        assert 'input' in node_types
        assert 'process' in node_types
        assert 'output' in node_types
        
        # Verify function name appears in process node
        process_nodes = [node for node in flow_diagram.nodes if node.get('type') == 'process']
        assert any(function_info.name in node.get('label', '') for node in process_nodes)
        
        # Verify edges connect properly
        edge_froms = [edge.get('from') for edge in flow_diagram.edges]
        edge_tos = [edge.get('to') for edge in flow_diagram.edges]
        assert 'input' in edge_froms or any('param_' in ef for ef in edge_froms)
        assert 'output' in edge_tos
        assert 'process' in edge_tos
        
        # If function has parameters, verify they are represented
        if function_info.parameters:
            param_nodes = [node for node in flow_diagram.nodes if node.get('type') == 'parameter']
            assert len(param_nodes) == len(function_info.parameters)
    
    @given(generate_code_sample(), st.sampled_from(['modern', 'classic', 'minimal']))
    def test_algorithm_flowchart_consistency(self, code, style):
        """
        Property 4.4: Algorithm flowchart consistency
        
        For any algorithm code and any style, the Visual_Documentation should 
        create flowcharts with consistent styling.
        
        **Validates: Requirements 4.4, 4.5**
        """
        visual_doc = VisualDocumentation(style=style)
        
        # Generate algorithm flowchart
        flowchart = visual_doc.create_algorithm_flowchart(code)
        
        # Verify flowchart structure (4.4)
        assert isinstance(flowchart, Flowchart)
        assert flowchart.title is not None
        assert len(flowchart.title.strip()) > 0
        assert len(flowchart.steps) > 0
        
        # Verify each step has required fields
        for step in flowchart.steps:
            assert 'id' in step
            assert 'type' in step
            assert 'description' in step
            assert 'line_number' in step
            assert step['line_number'] > 0
        
        # Verify connections are logical
        if len(flowchart.steps) > 1:
            assert len(flowchart.connections) >= len(flowchart.steps) - 1
            
            # Verify connection structure
            for connection in flowchart.connections:
                assert 'from' in connection
                assert 'to' in connection
                
                # Verify referenced steps exist
                step_ids = [step['id'] for step in flowchart.steps]
                assert connection['from'] in step_ids
                assert connection['to'] in step_ids
        
        # Verify step types are appropriate
        valid_step_types = ['start', 'end', 'process', 'decision', 'loop', 'output']
        for step in flowchart.steps:
            assert step['type'] in valid_step_types
    
    @given(generate_data_structure(), st.sampled_from(['modern', 'classic', 'minimal']))
    def test_data_structure_visualization_consistency(self, data, style):
        """
        Property 4.3: Data structure visualization consistency
        
        For any data structure and any style, the Visual_Documentation should 
        provide visual representations with consistent styling.
        
        **Validates: Requirements 4.3, 4.5**
        """
        visual_doc = VisualDocumentation(style=style)
        
        # Generate data structure visualization
        struct_diagram = visual_doc.visualize_data_structure(data)
        
        # Verify diagram structure (4.3)
        assert isinstance(struct_diagram, StructureDiagram)
        assert struct_diagram.structure_type is not None
        assert struct_diagram.visualization is not None
        assert struct_diagram.title is not None
        
        # Verify structure type matches data type
        if data is None:
            assert struct_diagram.structure_type == "None"
        elif isinstance(data, bool):  # Check bool before int since bool is subclass of int
            assert struct_diagram.structure_type == "bool"
        elif isinstance(data, int):
            assert struct_diagram.structure_type == "int"
        elif isinstance(data, list):
            assert struct_diagram.structure_type == "list"
        elif isinstance(data, tuple):
            assert struct_diagram.structure_type == "tuple"
        elif isinstance(data, dict):
            assert struct_diagram.structure_type == "dict"
        elif isinstance(data, set):
            assert struct_diagram.structure_type == "set"
        elif isinstance(data, str):
            assert struct_diagram.structure_type == "string"
        elif isinstance(data, float):
            assert struct_diagram.structure_type == "float"
        
        # Verify visualization is meaningful
        assert len(struct_diagram.visualization.strip()) > 0
        
        # For collections, verify size information is included when appropriate
        if isinstance(data, (list, tuple, dict, set)) and len(data) > 10:
            assert "..." in struct_diagram.visualization
            assert "total" in struct_diagram.visualization
    
    @given(generate_code_sample(), generate_data_structure(), st.sampled_from(['modern', 'classic', 'minimal']))
    def test_example_visualization_consistency(self, code, result, style):
        """
        Property 4.3: Example visualization consistency
        
        For any code example and result, the Visual_Documentation should 
        create consistent visual representations.
        
        **Validates: Requirements 4.3, 4.5**
        """
        visual_doc = VisualDocumentation(style=style)
        
        # Generate example visualization
        html_viz = visual_doc.create_example_visualization(code, result)
        
        # Verify HTML structure (4.3)
        assert isinstance(html_viz, str)
        assert len(html_viz.strip()) > 0
        
        # Verify required HTML elements are present
        assert '<div class="example-visualization">' in html_viz
        assert '<div class="example-header">' in html_viz
        assert '<div class="code-section">' in html_viz
        assert '<div class="result-section">' in html_viz
        assert '<style>' in html_viz
        
        # Verify code is properly escaped and included
        # The _escape_html method escapes single quotes as &#x27;
        escaped_code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace("'", '&#x27;').replace('"', '&quot;')
        assert escaped_code in html_viz
        
        # Verify result visualization is included
        result_viz = visual_doc.visualize_data_structure(result)
        escaped_result = result_viz.visualization.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
        assert escaped_result in html_viz
        
        # Verify style-specific CSS is applied (4.5)
        if style == "modern":
            assert "#01579b" in html_viz or "#4a148c" in html_viz
        elif style == "classic":
            assert "#e65100" in html_viz or "#880e4f" in html_viz
        
        # Verify consistent structure across all styles
        assert 'font-family:' in html_viz
        assert 'background:' in html_viz
        assert 'border:' in html_viz
    
    @given(
        st.lists(st.text(min_size=1, max_size=15, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))), min_size=1, max_size=5),
        st.sampled_from(['modern', 'classic', 'minimal'])
    )
    def test_consistent_styling_across_diagram_types(self, modules, style):
        """
        Property 4.5: Consistent styling across all visual elements
        
        For any visual documentation elements and any style, all diagrams 
        should maintain consistent styling themes.
        
        **Validates: Requirements 4.5**
        """
        # Filter valid modules
        valid_modules = [m for m in modules if m.isidentifier()]
        assume(len(valid_modules) > 0)
        
        visual_doc = VisualDocumentation(style=style)
        
        # Generate different types of diagrams
        arch_diagram = visual_doc.create_architecture_diagram(valid_modules)
        
        # Apply styling to all diagrams
        styled_arch = visual_doc.apply_consistent_styling(arch_diagram)
        
        # Verify consistent theme application
        diagrams = [styled_arch]
        
        # All diagrams should have theme configuration
        for diagram in diagrams:
            assert "%%{init:" in diagram.content
            
        # Verify style-specific consistency
        if style == "modern":
            color_palette = ["#e1f5fe", "#01579b", "#4a148c", "#f3e5f5"]
            for diagram in diagrams:
                # At least one color from the modern palette should be present
                assert any(color in diagram.content for color in color_palette)
        elif style == "classic":
            color_palette = ["#fff3e0", "#e65100", "#880e4f", "#fce4ec"]
            for diagram in diagrams:
                # At least one color from the classic palette should be present
                assert any(color in diagram.content for color in color_palette)
        else:  # minimal
            # Minimal style should have more neutral colors
            neutral_indicators = ["#f5f5f5", "#333", "#666", "#999"]
            for diagram in diagrams:
                assert any(indicator in diagram.content for indicator in neutral_indicators)
    
    def test_visual_documentation_error_handling(self):
        """
        Test that visual documentation handles edge cases gracefully.
        
        Validates that the system provides meaningful errors for invalid inputs
        while maintaining consistency.
        """
        visual_doc = VisualDocumentation()
        
        # Test empty module list
        with pytest.raises(ValueError, match="At least one module must be provided"):
            visual_doc.create_architecture_diagram([])
        
        # Test empty code
        with pytest.raises(ValueError, match="Code cannot be empty"):
            visual_doc.create_algorithm_flowchart("")
        
        with pytest.raises(ValueError, match="Code cannot be empty"):
            visual_doc.create_example_visualization("", "result")
        
        # Test empty diagram content
        empty_diagram = MermaidDiagram(DiagramType.ARCHITECTURE, "", "Test")
        with pytest.raises(ValueError, match="Diagram content cannot be empty"):
            visual_doc.apply_consistent_styling(empty_diagram)
        
        # Test function with empty name
        empty_func = FunctionInfo("", None, {}, None, "/path", 1)
        with pytest.raises(ValueError, match="Function must have a name"):
            visual_doc.generate_data_flow_diagram(empty_func)