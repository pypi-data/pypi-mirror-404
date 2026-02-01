"""
Visual documentation generator with diagrams and charts.
"""

from typing import List, Any, Optional
from .models import (
    MermaidDiagram, FlowDiagram, Flowchart, StructureDiagram,
    FunctionInfo, DiagramType
)


class VisualDocumentation:
    """
    Creates visual elements for documentation including diagrams and charts.
    
    Generates architecture diagrams, data flow charts, and algorithm
    flowcharts using Mermaid and other visualization tools.
    """
    
    # HTML tag constants
    DIV_CLOSE = '</div>'
    DIV_OPEN = '<div>'
    
    def __init__(self, style: str = "modern"):
        """
        Initialize the visual documentation generator.
        
        Args:
            style: Visual style for diagrams ("modern", "classic", "minimal")
        """
        self.style = style
    
    def create_architecture_diagram(self, modules: List[str]) -> MermaidDiagram:
        """
        Create an architecture diagram showing module relationships.
        
        Args:
            modules: List of module names to include
            
        Returns:
            MermaidDiagram: Generated architecture diagram
        """
        if not modules:
            raise ValueError("At least one module must be provided")
        
        # Generate Mermaid graph syntax for architecture
        lines = ["graph TB"]
        
        # Add nodes for each module
        for i, module in enumerate(modules):
            node_id = f"M{i}"
            lines.append(f'    {node_id}["{module}"]')
        
        # Add relationships based on common patterns
        for i, module in enumerate(modules):
            node_id = f"M{i}"
            # Connect related modules (simple heuristic based on naming)
            for j, other_module in enumerate(modules):
                if i != j:
                    other_id = f"M{j}"
                    # Connect if one module is a submodule of another
                    if module.startswith(other_module + ".") or other_module.startswith(module + "."):
                        lines.append(f"    {other_id} --> {node_id}")
        
        # Apply styling based on selected style
        if self.style == "modern":
            lines.extend([
                "    classDef default fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
                "    classDef highlight fill:#f3e5f5,stroke:#4a148c,stroke-width:3px"
            ])
        elif self.style == "classic":
            lines.extend([
                "    classDef default fill:#fff3e0,stroke:#e65100,stroke-width:2px",
                "    classDef highlight fill:#fce4ec,stroke:#880e4f,stroke-width:3px"
            ])
        
        content = "\n".join(lines)
        return MermaidDiagram(
            diagram_type=DiagramType.ARCHITECTURE,
            content=content,
            title="Module Architecture"
        )
    
    def generate_data_flow_diagram(self, function: FunctionInfo) -> FlowDiagram:
        """
        Generate a data flow diagram for a function.
        
        Args:
            function: Function information
            
        Returns:
            FlowDiagram: Generated data flow diagram
        """
        if not function.name:
            raise ValueError("Function must have a name")
        
        nodes = []
        edges = []
        
        # Input node
        input_node = {
            "id": "input",
            "label": "Input Parameters",
            "type": "input",
            "details": ", ".join(function.parameters.keys()) if function.parameters else "None"
        }
        nodes.append(input_node)
        
        # Function processing node
        process_node = {
            "id": "process",
            "label": function.name,
            "type": "process",
            "details": function.docstring[:50] + "..." if function.docstring and len(function.docstring) > 50 else function.docstring or ""
        }
        nodes.append(process_node)
        
        # Output node
        output_node = {
            "id": "output", 
            "label": "Return Value",
            "type": "output",
            "details": function.return_type or "Any"
        }
        nodes.append(output_node)
        
        # Connect the nodes
        edges.append({"from": "input", "to": "process", "label": "parameters"})
        edges.append({"from": "process", "to": "output", "label": "result"})
        
        # Add parameter-specific flows if we have detailed parameter info
        if function.parameters:
            for i, (param_name, param_type) in enumerate(function.parameters.items()):
                param_id = f"param_{i}"
                param_node = {
                    "id": param_id,
                    "label": param_name,
                    "type": "parameter",
                    "details": param_type
                }
                nodes.append(param_node)
                edges.append({"from": param_id, "to": "process", "label": param_type})
        
        return FlowDiagram(
            nodes=nodes,
            edges=edges,
            title=f"Data Flow: {function.name}"
        )
    
    def create_algorithm_flowchart(self, code: str, title: Optional[str] = None) -> Flowchart:
        """
        Create a flowchart for an algorithm.
        
        Args:
            code: Python code to analyze
            title: Optional title for the flowchart
            
        Returns:
            Flowchart: Generated algorithm flowchart
        """
        if not code.strip():
            raise ValueError("Code cannot be empty")
        
        steps = []
        connections = []
        
        # Simple code analysis - split by lines and identify key structures
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            step_id = f"step_{i}"
            step_type, description = self._analyze_code_line(line)
            
            steps.append({
                "id": step_id,
                "type": step_type,
                "description": description,
                "line_number": i + 1
            })
            
            # Connect to previous step (simple linear flow)
            if i > 0:
                connections.append({
                    "from": f"step_{i - 1}",
                    "to": step_id,
                    "label": ""
                })
        
        # Generate title if not provided
        if title is None:
            title = self._generate_flowchart_title(lines)
        
        return Flowchart(
            steps=steps,
            connections=connections,
            title=title
        )
    
    def _analyze_code_line(self, line: str) -> tuple[str, str]:
        """Analyze a line of code and return its type and description."""
        if line.startswith('def '):
            return "start", f"Function: {line}"
        elif line.startswith('if '):
            return "decision", f"Decision: {line}"
        elif line.startswith('elif '):
            return "decision", f"Alternative: {line}"
        elif line.startswith('else:'):
            return "decision", "Else branch"
        elif line.startswith('for ') or line.startswith('while '):
            return "loop", f"Loop: {line}"
        elif line.startswith('return '):
            return "end", f"Return: {line}"
        elif line.startswith('print(') or 'print(' in line:
            return "output", f"Output: {line}"
        else:
            return "process", line
    
    def _generate_flowchart_title(self, lines: List[str]) -> str:
        """Generate a title for the flowchart based on the code."""
        if not lines:
            return "Algorithm Flowchart"
        
        first_line = lines[0]
        if first_line.startswith('def '):
            func_name = first_line.split('(')[0].replace('def ', '')
            return f"Algorithm: {func_name}"
        else:
            return "Algorithm Flowchart"
        """
        Create a flowchart for an algorithm.
        
        Args:
            code: Python code to analyze
            title: Optional title for the flowchart
            
        Returns:
            Flowchart: Generated algorithm flowchart
        """
        if not code.strip():
            raise ValueError("Code cannot be empty")
        
        steps = []
        connections = []
        
        # Simple code analysis - split by lines and identify key structures
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        
        step_counter = 0
        
        for i, line in enumerate(lines):
            step_id = f"step_{step_counter}"
            
            # Identify different types of statements
            if line.startswith('def '):
                step_type = "start"
                description = f"Function: {line}"
            elif line.startswith('if '):
                step_type = "decision"
                description = f"Decision: {line}"
            elif line.startswith('elif '):
                step_type = "decision"
                description = f"Alternative: {line}"
            elif line.startswith('else:'):
                step_type = "decision"
                description = "Else branch"
            elif line.startswith('for ') or line.startswith('while '):
                step_type = "loop"
                description = f"Loop: {line}"
            elif line.startswith('return '):
                step_type = "end"
                description = f"Return: {line}"
            elif line.startswith('print(') or 'print(' in line:
                step_type = "output"
                description = f"Output: {line}"
            else:
                step_type = "process"
                description = line
            
            steps.append({
                "id": step_id,
                "type": step_type,
                "description": description,
                "line_number": i + 1
            })
            
            # Connect to previous step (simple linear flow)
            if step_counter > 0:
                connections.append({
                    "from": f"step_{step_counter - 1}",
                    "to": step_id,
                    "label": ""
                })
            
            step_counter += 1
        
        # If no title provided, generate one
        if title is None:
            # Try to extract function name from first line
            first_line = lines[0] if lines else ""
            if first_line.startswith('def '):
                func_name = first_line.split('(')[0].replace('def ', '')
                title = f"Algorithm: {func_name}"
            else:
                title = "Algorithm Flowchart"
        
        return Flowchart(
            steps=steps,
            connections=connections,
            title=title
        )
    
    def visualize_data_structure(self, data: Any, title: Optional[str] = None) -> StructureDiagram:
        """
        Create a visual representation of a data structure.
        
        Args:
            data: Data structure to visualize
            title: Optional title for the diagram
            
        Returns:
            StructureDiagram: Generated structure diagram
        """
        structure_type, visualization = self._get_structure_info(data)
        
        if title is None:
            title = f"{structure_type.title()} Visualization"
        
        return StructureDiagram(
            structure_type=structure_type,
            data=data,
            visualization=visualization,
            title=title
        )
    
    def _get_structure_info(self, data: Any) -> tuple[str, str]:
        """Get structure type and visualization for data."""
        if data is None:
            return "None", "null"
        elif isinstance(data, (list, tuple)):
            return self._visualize_sequence(data)
        elif isinstance(data, dict):
            return self._visualize_dict(data)
        elif isinstance(data, set):
            return self._visualize_set(data)
        elif isinstance(data, str):
            return self._visualize_string(data)
        elif isinstance(data, (int, float, bool)):
            return type(data).__name__, str(data)
        else:
            return type(data).__name__, f"<{type(data).__name__} object>"
    
    def _visualize_sequence(self, data) -> tuple[str, str]:
        """Visualize list or tuple."""
        structure_type = "list" if isinstance(data, list) else "tuple"
        if len(data) <= 10:
            items = [str(item) for item in data]
            visualization = f"[{', '.join(items)}]"
        else:
            items = [str(item) for item in data[:5]]
            visualization = f"[{', '.join(items)}, ... ({len(data)} items total)]"
        return structure_type, visualization
    
    def _visualize_dict(self, data: dict) -> tuple[str, str]:
        """Visualize dictionary."""
        if len(data) <= 5:
            items = [f"'{k}': {repr(v)}" for k, v in data.items()]
            visualization = f"{{{', '.join(items)}}}"
        else:
            items = [f"'{k}': {repr(v)}" for k, v in list(data.items())[:3]]
            visualization = f"{{{', '.join(items)}, ... ({len(data)} keys total)}}"
        return "dict", visualization
    
    def _visualize_set(self, data: set) -> tuple[str, str]:
        """Visualize set."""
        if len(data) <= 5:
            items = [str(item) for item in data]
            visualization = f"{{{', '.join(items)}}}"
        else:
            items = [str(item) for item in list(data)[:3]]
            visualization = f"{{{', '.join(items)}, ... ({len(data)} items total)}}"
        return "set", visualization
    
    def _visualize_string(self, data: str) -> tuple[str, str]:
        """Visualize string."""
        if len(data) <= 50:
            visualization = f'"{data}"'
        else:
            visualization = f'"{data[:47]}..." ({len(data)} chars)'
        return "string", visualization
        """
        Create a visual representation of a data structure.
        
        Args:
            data: Data structure to visualize
            title: Optional title for the diagram
            
        Returns:
            StructureDiagram: Generated structure diagram
        """
        if data is None:
            structure_type = "None"
            visualization = "null"
        elif isinstance(data, (list, tuple)):
            structure_type = "list" if isinstance(data, list) else "tuple"
            # Create a simple text-based visualization
            if len(data) <= 10:
                items = [str(item) for item in data]
                visualization = f"[{', '.join(items)}]"
            else:
                items = [str(item) for item in data[:5]]
                visualization = f"[{', '.join(items)}, ... ({len(data)} items total)]"
        elif isinstance(data, dict):
            structure_type = "dict"
            if len(data) <= 5:
                items = [f"'{k}': {repr(v)}" for k, v in data.items()]
                visualization = f"{{{', '.join(items)}}}"
            else:
                items = [f"'{k}': {repr(v)}" for k, v in list(data.items())[:3]]
                visualization = f"{{{', '.join(items)}, ... ({len(data)} keys total)}}"
        elif isinstance(data, set):
            structure_type = "set"
            if len(data) <= 5:
                items = [str(item) for item in data]
                visualization = f"{{{', '.join(items)}}}"
            else:
                items = [str(item) for item in list(data)[:3]]
                visualization = f"{{{', '.join(items)}, ... ({len(data)} items total)}}"
        elif isinstance(data, str):
            structure_type = "string"
            if len(data) <= 50:
                visualization = f'"{data}"'
            else:
                visualization = f'"{data[:47]}..." ({len(data)} chars)'
        elif isinstance(data, (int, float, bool)):
            structure_type = type(data).__name__
            visualization = str(data)
        else:
            structure_type = type(data).__name__
            visualization = f"<{structure_type} object>"
        
        if title is None:
            title = f"{structure_type.title()} Visualization"
        
        return StructureDiagram(
            structure_type=structure_type,
            data=data,
            visualization=visualization,
            title=title
        )
    
    def create_example_visualization(self, code: str, result: Any) -> str:
        """
        Create visual representation of code example results.
        
        Args:
            code: Example code
            result: Expected result
            
        Returns:
            str: HTML/SVG visualization of the example
        """
        if not code.strip():
            raise ValueError("Code cannot be empty")
        
        # Create a structured HTML visualization
        html_parts = []
        
        # Header
        html_parts.append('<div class="example-visualization">')
        html_parts.append('<div class="example-header">Code Example</div>')
        
        # Code section
        html_parts.append('<div class="code-section">')
        html_parts.append('<pre class="code-block">')
        html_parts.append(f'<code>{self._escape_html(code)}</code>')
        html_parts.append('</pre>')
        html_parts.append(self.DIV_CLOSE)
        
        # Arrow
        html_parts.append('<div class="arrow">↓</div>')
        
        # Result section
        html_parts.append('<div class="result-section">')
        html_parts.append('<div class="result-label">Result:</div>')
        
        # Visualize the result based on its type
        result_viz = self.visualize_data_structure(result)
        html_parts.append(f'<div class="result-content">{self._escape_html(result_viz.visualization)}</div>')
        html_parts.append(f'<div class="result-type">Type: {result_viz.structure_type}</div>')
        html_parts.append(self.DIV_CLOSE)
        
        # Styling
        html_parts.append(self._get_example_styles())
        
        html_parts.append(self.DIV_CLOSE)
        
        return '\n'.join(html_parts)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def _get_example_styles(self) -> str:
        """Get CSS styles for example visualization."""
        if self.style == "modern":
            return '''
<style>
.example-visualization {
    border: 2px solid #01579b;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
    background: linear-gradient(135deg, #e1f5fe 0%, #f3e5f5 100%);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.example-header {
    font-weight: bold;
    color: #01579b;
    margin-bottom: 12px;
    font-size: 1.1em;
}
.code-section {
    background: #263238;
    border-radius: 4px;
    padding: 12px;
    margin: 8px 0;
}
.code-block {
    color: #e8eaf6;
    margin: 0;
    font-family: 'Courier New', monospace;
}
.arrow {
    text-align: center;
    font-size: 1.5em;
    color: #4a148c;
    margin: 8px 0;
}
.result-section {
    background: #f8f9fa;
    border-radius: 4px;
    padding: 12px;
    border-left: 4px solid #4a148c;
}
.result-label {
    font-weight: bold;
    color: #4a148c;
    margin-bottom: 8px;
}
.result-content {
    font-family: 'Courier New', monospace;
    background: #ffffff;
    padding: 8px;
    border-radius: 3px;
    border: 1px solid #e0e0e0;
}
.result-type {
    font-size: 0.9em;
    color: #666;
    margin-top: 4px;
    font-style: italic;
}
</style>'''
        elif self.style == "classic":
            return '''
<style>
.example-visualization {
    border: 1px solid #e65100;
    padding: 12px;
    margin: 12px 0;
    background: #fff3e0;
    font-family: serif;
}
.example-header {
    font-weight: bold;
    color: #e65100;
    margin-bottom: 8px;
}
.code-section {
    background: #f5f5f5;
    padding: 8px;
    margin: 6px 0;
    border: 1px solid #ccc;
}
.code-block {
    margin: 0;
    font-family: monospace;
}
.arrow {
    text-align: center;
    font-size: 1.2em;
    color: #880e4f;
    margin: 6px 0;
}
.result-section {
    background: #fce4ec;
    padding: 8px;
    border: 1px solid #880e4f;
}
.result-label {
    font-weight: bold;
    color: #880e4f;
    margin-bottom: 6px;
}
.result-content {
    font-family: monospace;
    background: #ffffff;
    padding: 6px;
    border: 1px solid #ccc;
}
.result-type {
    font-size: 0.85em;
    color: #666;
    margin-top: 3px;
}
</style>'''
        else:  # minimal
            return '''
<style>
.example-visualization {
    border: 1px solid #ccc;
    padding: 8px;
    margin: 8px 0;
    background: #fafafa;
}
.example-header {
    font-weight: bold;
    margin-bottom: 6px;
}
.code-section {
    background: #f0f0f0;
    padding: 6px;
    margin: 4px 0;
}
.code-block {
    margin: 0;
    font-family: monospace;
}
.arrow {
    text-align: center;
    margin: 4px 0;
}
.result-section {
    background: #f9f9f9;
    padding: 6px;
}
.result-label {
    font-weight: bold;
    margin-bottom: 4px;
}
.result-content {
    font-family: monospace;
    background: #ffffff;
    padding: 4px;
    border: 1px solid #ddd;
}
.result-type {
    font-size: 0.8em;
    color: #666;
    margin-top: 2px;
}
</style>'''
    
    def apply_consistent_styling(self, diagram: MermaidDiagram) -> MermaidDiagram:
        """
        Apply consistent styling to a diagram.
        
        Args:
            diagram: Diagram to style
            
        Returns:
            MermaidDiagram: Styled diagram
        """
        if not diagram.content:
            raise ValueError("Diagram content cannot be empty")
        
        styled_content = diagram.content
        
        # Add theme configuration if not present
        if "%%{init:" not in styled_content:
            theme_config = self._get_theme_config()
            styled_content = theme_config + "\n" + styled_content
        
        # Add diagram-specific styling
        styled_content = self._add_diagram_specific_styling(diagram, styled_content)
        
        return MermaidDiagram(
            diagram_type=diagram.diagram_type,
            content=styled_content,
            title=diagram.title
        )
    
    def _get_theme_config(self) -> str:
        """Get theme configuration based on style."""
        theme_configs = {
            "modern": '''%%{init: {"theme": "base", "themeVariables": {
    "primaryColor": "#e1f5fe",
    "primaryTextColor": "#01579b", 
    "primaryBorderColor": "#01579b",
    "lineColor": "#4a148c",
    "secondaryColor": "#f3e5f5",
    "tertiaryColor": "#fff"
}}}%%''',
            "classic": '''%%{init: {"theme": "base", "themeVariables": {
    "primaryColor": "#fff3e0",
    "primaryTextColor": "#e65100",
    "primaryBorderColor": "#e65100", 
    "lineColor": "#880e4f",
    "secondaryColor": "#fce4ec",
    "tertiaryColor": "#fff"
}}}%%''',
            "minimal": '''%%{init: {"theme": "base", "themeVariables": {
    "primaryColor": "#f5f5f5",
    "primaryTextColor": "#333",
    "primaryBorderColor": "#666",
    "lineColor": "#999",
    "secondaryColor": "#fafafa",
    "tertiaryColor": "#fff"
}}}%%'''
        }
        return theme_configs.get(self.style, theme_configs["minimal"])
    
    def _add_diagram_specific_styling(self, diagram: MermaidDiagram, content: str) -> str:
        """Add styling specific to diagram type."""
        if diagram.diagram_type == DiagramType.ARCHITECTURE and "classDef" not in content:
            return content + self._get_architecture_styling()
        elif diagram.diagram_type == DiagramType.DATA_FLOW and "linkStyle" not in content:
            return content + self._get_data_flow_styling()
        return content
    
    def _get_architecture_styling(self) -> str:
        """Get architecture-specific styling."""
        style_map = {
            "modern": "\n    classDef default fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
            "classic": "\n    classDef default fill:#fff3e0,stroke:#e65100,stroke-width:2px",
            "minimal": "\n    classDef default fill:#f5f5f5,stroke:#666,stroke-width:1px"
        }
        return style_map.get(self.style, style_map["minimal"])
    
    def _get_data_flow_styling(self) -> str:
        """Get data flow-specific styling."""
        style_map = {
            "modern": "\n    linkStyle default stroke:#4a148c,stroke-width:2px",
            "classic": "\n    linkStyle default stroke:#880e4f,stroke-width:2px",
            "minimal": "\n    linkStyle default stroke:#999,stroke-width:1px"
        }
        return style_map.get(self.style, style_map["minimal"])
        """
        Apply consistent styling to a diagram.
        
        Args:
            diagram: Diagram to style
            
        Returns:
            MermaidDiagram: Styled diagram
        """
        if not diagram.content:
            raise ValueError("Diagram content cannot be empty")
        
        # Apply styling based on diagram type and selected style
        styled_content = diagram.content
        
        # Add theme directive at the beginning if not present
        if "%%{init:" not in styled_content:
            if self.style == "modern":
                theme_config = '''%%{init: {"theme": "base", "themeVariables": {
    "primaryColor": "#e1f5fe",
    "primaryTextColor": "#01579b", 
    "primaryBorderColor": "#01579b",
    "lineColor": "#4a148c",
    "secondaryColor": "#f3e5f5",
    "tertiaryColor": "#fff"
}}}%%'''
            elif self.style == "classic":
                theme_config = '''%%{init: {"theme": "base", "themeVariables": {
    "primaryColor": "#fff3e0",
    "primaryTextColor": "#e65100",
    "primaryBorderColor": "#e65100", 
    "lineColor": "#880e4f",
    "secondaryColor": "#fce4ec",
    "tertiaryColor": "#fff"
}}}%%'''
            else:  # minimal
                theme_config = '''%%{init: {"theme": "base", "themeVariables": {
    "primaryColor": "#f5f5f5",
    "primaryTextColor": "#333",
    "primaryBorderColor": "#666",
    "lineColor": "#999",
    "secondaryColor": "#fafafa",
    "tertiaryColor": "#fff"
}}}%%'''
            
            styled_content = theme_config + "\n" + styled_content
        
        # Add diagram-specific styling
        if diagram.diagram_type == DiagramType.ARCHITECTURE:
            # Ensure architecture diagrams have proper node styling
            if "classDef" not in styled_content:
                if self.style == "modern":
                    styled_content += "\n    classDef default fill:#e1f5fe,stroke:#01579b,stroke-width:2px"
                elif self.style == "classic":
                    styled_content += "\n    classDef default fill:#fff3e0,stroke:#e65100,stroke-width:2px"
                else:
                    styled_content += "\n    classDef default fill:#f5f5f5,stroke:#666,stroke-width:1px"
        
        elif diagram.diagram_type == DiagramType.DATA_FLOW:
            # Add flow-specific styling
            if "linkStyle" not in styled_content:
                if self.style == "modern":
                    styled_content += "\n    linkStyle default stroke:#4a148c,stroke-width:2px"
                elif self.style == "classic":
                    styled_content += "\n    linkStyle default stroke:#880e4f,stroke-width:2px"
                else:
                    styled_content += "\n    linkStyle default stroke:#999,stroke-width:1px"
        
        return MermaidDiagram(
            diagram_type=diagram.diagram_type,
            content=styled_content,
            title=diagram.title
        )