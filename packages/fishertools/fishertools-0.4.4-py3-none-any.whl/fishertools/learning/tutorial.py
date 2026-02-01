"""
Tutorial Engine for generating step-by-step explanations and interactive lessons.
"""

import ast
import re
import uuid
from typing import List, Optional, Dict, Any, Tuple
from .models import (
    StepExplanation, InteractiveExercise, ValidationResult, 
    CodeContext, DifficultyLevel, ExerciseStatus
)


class TutorialEngine:
    """
    Generates step-by-step explanations and creates interactive exercises.
    
    Provides detailed code explanations with examples and creates
    interactive learning experiences for beginners.
    """
    
    def __init__(self):
        """Initialize the tutorial engine."""
        # Integration point for example repository
        self._example_repository = None
        
        # Code pattern explanations for different constructs
        self._code_patterns = {
            'variable_assignment': {
                'pattern': r'^(\w+)\s*=\s*(.+)$',
                'explanation': "Variable assignment: storing the value {value} in variable '{var}'",
                'concepts': ['variables', 'assignment', 'data_storage']
            },
            'function_call': {
                'pattern': r'(\w+)\s*\([^)]*\)',
                'explanation': "Function call: executing the function '{func}' with given arguments",
                'concepts': ['functions', 'function_calls', 'execution']
            },
            'list_creation': {
                'pattern': r'\[.*\]',
                'explanation': "List creation: making a new list containing the specified items",
                'concepts': ['lists', 'data_structures', 'collections']
            },
            'dict_creation': {
                'pattern': r'\{.*\}',
                'explanation': "Dictionary creation: making a new dictionary with key-value pairs",
                'concepts': ['dictionaries', 'data_structures', 'key_value_pairs']
            },
            'for_loop': {
                'pattern': r'^for\s+\w+\s+in\s+.+:',
                'explanation': "For loop: repeating code for each item in the collection",
                'concepts': ['loops', 'iteration', 'control_flow']
            },
            'if_statement': {
                'pattern': r'^if\s+.+:',
                'explanation': "Conditional statement: executing code only if the condition is true",
                'concepts': ['conditionals', 'boolean_logic', 'control_flow']
            },
            'function_definition': {
                'pattern': r'^def\s+(\w+)\s*\([^)]*\):',
                'explanation': "Function definition: creating a reusable block of code named '{func}'",
                'concepts': ['functions', 'definition', 'code_organization']
            },
            'import_statement': {
                'pattern': r'^(from\s+\w+\s+)?import\s+.+',
                'explanation': "Import statement: bringing in code from other modules or libraries",
                'concepts': ['imports', 'modules', 'libraries']
            },
            'print_statement': {
                'pattern': r'print\s*\([^)]*\)',
                'explanation': "Print statement: displaying output to the user",
                'concepts': ['output', 'display', 'debugging']
            }
        }
        
        # Exercise templates by topic and difficulty
        self._exercise_templates = {
            'variables': {
                DifficultyLevel.BEGINNER: {
                    'title': 'Basic Variable Assignment',
                    'description': 'Practice creating and using variables to store different types of data.',
                    'starter_code': '# Create a variable called "name" and assign your name to it\n# Then create a variable called "age" and assign your age\n',
                    'solution': 'name = "Alice"\nage = 25',
                    'hints': [
                        'Use quotes around text values (strings)',
                        'Numbers don\'t need quotes',
                        'Variable names should be descriptive'
                    ]
                },
                DifficultyLevel.INTERMEDIATE: {
                    'title': 'Variable Operations',
                    'description': 'Practice performing operations with variables and updating their values.',
                    'starter_code': '# Create two number variables and calculate their sum\n# Store the result in a new variable\n',
                    'solution': 'num1 = 10\nnum2 = 20\nsum_result = num1 + num2',
                    'hints': [
                        'Use meaningful variable names',
                        'You can use variables in calculations',
                        'Store the result in a new variable'
                    ]
                }
            },
            'lists': {
                DifficultyLevel.BEGINNER: {
                    'title': 'Creating and Using Lists',
                    'description': 'Practice creating lists and accessing their elements.',
                    'starter_code': '# Create a list of your favorite fruits\n# Then print the first fruit in the list\n',
                    'solution': 'fruits = ["apple", "banana", "orange"]\nprint(fruits[0])',
                    'hints': [
                        'Use square brackets [] to create a list',
                        'Separate items with commas',
                        'Use index [0] to get the first item'
                    ]
                },
                DifficultyLevel.INTERMEDIATE: {
                    'title': 'List Operations',
                    'description': 'Practice adding, removing, and modifying list elements.',
                    'starter_code': '# Create a list of numbers\n# Add a new number to the end\n# Remove the first number\n',
                    'solution': 'numbers = [1, 2, 3]\nnumbers.append(4)\nnumbers.pop(0)',
                    'hints': [
                        'Use append() to add to the end',
                        'Use pop(0) to remove the first item',
                        'Lists are mutable (can be changed)'
                    ]
                }
            },
            'functions': {
                DifficultyLevel.BEGINNER: {
                    'title': 'Simple Function Definition',
                    'description': 'Practice defining and calling a simple function.',
                    'starter_code': '# Define a function called "greet" that prints "Hello!"\n# Then call the function\n',
                    'solution': 'def greet():\n    print("Hello!")\n\ngreet()',
                    'hints': [
                        'Use "def" to define a function',
                        'Don\'t forget the colon (:) after the function name',
                        'Indent the function body',
                        'Call the function by using its name with parentheses'
                    ]
                },
                DifficultyLevel.INTERMEDIATE: {
                    'title': 'Function with Parameters',
                    'description': 'Practice creating functions that accept parameters and return values.',
                    'starter_code': '# Define a function that takes a name parameter and returns a greeting\n# Call the function with your name\n',
                    'solution': 'def greet(name):\n    return f"Hello, {name}!"\n\nresult = greet("Alice")',
                    'hints': [
                        'Put parameter names inside the parentheses',
                        'Use "return" to send a value back',
                        'Store the returned value in a variable'
                    ]
                }
            },
            'loops': {
                DifficultyLevel.BEGINNER: {
                    'title': 'Simple For Loop',
                    'description': 'Practice using a for loop to iterate through a list.',
                    'starter_code': '# Create a list of colors\n# Use a for loop to print each color\n',
                    'solution': 'colors = ["red", "green", "blue"]\nfor color in colors:\n    print(color)',
                    'hints': [
                        'Use "for item in list:" syntax',
                        'Don\'t forget the colon (:)',
                        'Indent the loop body',
                        'The loop variable takes each value from the list'
                    ]
                }
            }
        }
    
    def generate_step_explanation(self, code_line: str, context: Optional[CodeContext] = None) -> StepExplanation:
        """
        Generate detailed explanation for a single line of code.
        
        Args:
            code_line: Single line of Python code to explain
            context: Context information about the code
            
        Returns:
            StepExplanation: Detailed explanation with examples
        """
        if not code_line or not isinstance(code_line, str):
            raise ValueError("Code line must be a non-empty string")
        
        code_line = code_line.strip()
        if not code_line:
            raise ValueError("Code line cannot be empty or whitespace only")
        
        # Analyze the code line to determine its type and generate explanation
        explanation_data = self._analyze_code_line(code_line, context)
        
        # Generate input/output examples if possible
        input_example, output_example = self._generate_examples(code_line, explanation_data)
        
        return StepExplanation(
            step_number=1,  # Will be set by caller if needed
            description=explanation_data['description'],
            code_snippet=code_line,
            input_example=input_example,
            output_example=output_example,
            related_concepts=explanation_data['concepts'],
            visual_aid=explanation_data.get('visual_aid')
        )
    
    def create_interactive_exercise(self, topic: str, difficulty: DifficultyLevel = DifficultyLevel.BEGINNER) -> InteractiveExercise:
        """
        Create an interactive coding exercise for the given topic.
        
        Args:
            topic: Topic for the exercise (e.g., "lists", "functions")
            difficulty: Difficulty level for the exercise
            
        Returns:
            InteractiveExercise: A new interactive exercise
        """
        if not topic or not isinstance(topic, str):
            raise ValueError("Topic must be a non-empty string")
        
        topic_lower = topic.lower()
        
        # Get exercise template
        template = self._get_exercise_template(topic_lower, difficulty)
        
        return InteractiveExercise(
            id=str(uuid.uuid4()),
            title=template['title'],
            description=template['description'],
            starter_code=template['starter_code'],
            expected_output=template.get('solution', 'Correct implementation'),
            hints=template['hints'],
            difficulty_level=difficulty,
            topic=topic,
            status=ExerciseStatus.NOT_STARTED
        )
    
    def validate_solution(self, exercise: InteractiveExercise, solution: str) -> ValidationResult:
        """
        Validate a user's solution to an interactive exercise.
        
        Args:
            exercise: The exercise being solved
            solution: User's code solution
            
        Returns:
            ValidationResult: Validation result with feedback
        """
        if not solution or not isinstance(solution, str):
            return ValidationResult(
                is_correct=False,
                feedback="Solution cannot be empty",
                errors=["No code provided"],
                suggestions=["Please write some code to solve the exercise"]
            )
        
        # Basic syntax validation
        syntax_errors = self._check_syntax(solution)
        if syntax_errors:
            return ValidationResult(
                is_correct=False,
                feedback="Your code has syntax errors",
                errors=syntax_errors,
                suggestions=["Check your syntax", "Make sure all parentheses and brackets are closed"]
            )
        
        # Topic-specific validation
        validation_result = self._validate_topic_specific(exercise, solution)
        
        return validation_result
    
    def provide_hint(self, exercise: InteractiveExercise, attempt: str) -> str:
        """
        Provide a helpful hint based on the user's attempt.
        
        Args:
            exercise: The exercise being solved
            attempt: User's current attempt
            
        Returns:
            str: Helpful hint for the user
        """
        if not attempt or not attempt.strip():
            # No attempt yet, provide first hint
            if exercise.hints:
                return exercise.hints[0]
            return "Start by reading the exercise description carefully."
        
        # Analyze the attempt to provide specific hints
        attempt = attempt.strip()
        
        # Check for common issues and provide targeted hints
        if exercise.topic.lower() == 'variables':
            if '=' not in attempt:
                return "Remember to use the = sign to assign values to variables."
            if attempt.count('"') % 2 != 0:
                return "Make sure you have matching quotes around text values."
        
        elif exercise.topic.lower() == 'lists':
            if '[' not in attempt or ']' not in attempt:
                return "Use square brackets [] to create a list."
            if 'print' not in attempt.lower() and 'print' in exercise.description.lower():
                return "Don't forget to print the result as requested."
        
        elif exercise.topic.lower() == 'functions':
            if 'def' not in attempt:
                return "Use 'def' to define a function."
            if ':' not in attempt:
                return "Don't forget the colon (:) after the function definition."
            if not any(line.startswith('    ') for line in attempt.split('\n')):
                return "Remember to indent the function body."
        
        # Return next available hint or generic encouragement
        if exercise.attempts < len(exercise.hints):
            return exercise.hints[exercise.attempts]
        
        return "You're on the right track! Keep trying different approaches."
    
    def explain_solution(self, exercise: InteractiveExercise) -> List[StepExplanation]:
        """
        Provide detailed explanation of the exercise solution.
        
        Args:
            exercise: The completed exercise
            
        Returns:
            List[StepExplanation]: Step-by-step solution explanation
        """
        # Get the expected solution from exercise templates
        topic_lower = exercise.topic.lower()
        template = self._get_exercise_template(topic_lower, exercise.difficulty_level)
        solution_code = template.get('solution', exercise.expected_output)
        
        # Generate step-by-step explanations for the solution
        explanations = []
        lines = solution_code.split('\n')
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith('#'):  # Skip empty lines and comments
                explanation = self.generate_step_explanation(line)
                explanation.step_number = i
                explanations.append(explanation)
        
        return explanations
    
    def _analyze_code_line(self, code_line: str, context: Optional[CodeContext]) -> Dict[str, Any]:
        """Analyze a code line and determine its type and explanation."""
        code_line = code_line.strip()
        
        # Check against known patterns
        for pattern_name, pattern_info in self._code_patterns.items():
            if re.search(pattern_info['pattern'], code_line):
                description = pattern_info['explanation']
                
                # Extract specific information for templated explanations
                if pattern_name == 'variable_assignment':
                    match = re.match(pattern_info['pattern'], code_line)
                    if match:
                        var_name, value = match.groups()
                        description = description.format(var=var_name, value=value)
                
                elif pattern_name == 'function_call':
                    match = re.search(r'(\w+)\s*\(', code_line)
                    if match:
                        func_name = match.group(1)
                        description = description.format(func=func_name)
                
                elif pattern_name == 'function_definition':
                    match = re.match(pattern_info['pattern'], code_line)
                    if match:
                        func_name = match.group(1)
                        description = description.format(func=func_name)
                
                return {
                    'description': description,
                    'concepts': pattern_info['concepts'],
                    'pattern': pattern_name
                }
        
        # Default explanation for unrecognized patterns
        return {
            'description': f"Python code: {code_line}",
            'concepts': ['python_syntax'],
            'pattern': 'unknown'
        }
    
    def _generate_examples(self, code_line: str, explanation_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Generate input and output examples for a code line."""
        pattern = explanation_data.get('pattern', 'unknown')
        
        if pattern == 'variable_assignment':
            # Extract the assignment
            match = re.match(r'^(\w+)\s*=\s*(.+)$', code_line)
            if match:
                var_name, value = match.groups()
                return f"Before: {var_name} is undefined", f"After: {var_name} = {value}"
        
        elif pattern == 'print_statement':
            # Extract what's being printed
            match = re.search(r'print\s*\(([^)]*)\)', code_line)
            if match:
                content = match.group(1)
                return f"Input: {content}", f"Output: (printed to screen)"
        
        elif pattern == 'list_creation':
            return "Input: individual items", "Output: organized list structure"
        
        elif pattern == 'function_call':
            return "Input: function arguments", "Output: function result"
        
        return None, None
    
    def _get_exercise_template(self, topic: str, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """Get exercise template for topic and difficulty."""
        if topic in self._exercise_templates:
            topic_templates = self._exercise_templates[topic]
            if difficulty in topic_templates:
                return topic_templates[difficulty]
            # Fall back to beginner if difficulty not found
            return topic_templates.get(DifficultyLevel.BEGINNER, self._get_default_template(topic))
        
        # Return default template for unknown topics
        return self._get_default_template(topic)
    
    def _get_default_template(self, topic: str) -> Dict[str, Any]:
        """Get default exercise template for unknown topics."""
        return {
            'title': f'Practice with {topic.title()}',
            'description': f'Practice basic concepts related to {topic}.',
            'starter_code': f'# Write code to practice {topic}\n',
            'solution': f'# Solution for {topic} exercise',
            'hints': [
                'Read the exercise description carefully',
                'Start with simple examples',
                'Test your code step by step'
            ]
        }
    
    def _check_syntax(self, code: str) -> List[str]:
        """Check code for syntax errors."""
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error on line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"Code error: {str(e)}")
        
        return errors
    
    def _validate_topic_specific(self, exercise: InteractiveExercise, solution: str) -> ValidationResult:
        """Perform topic-specific validation of the solution."""
        topic = exercise.topic.lower()
        
        if topic == 'variables':
            return self._validate_variables_exercise(exercise, solution)
        elif topic == 'lists':
            return self._validate_lists_exercise(exercise, solution)
        elif topic == 'functions':
            return self._validate_functions_exercise(exercise, solution)
        elif topic == 'loops':
            return self._validate_loops_exercise(exercise, solution)
        else:
            # Generic validation
            return ValidationResult(
                is_correct=True,
                feedback="Code looks good! Well done.",
                suggestions=["Keep practicing to improve your skills"]
            )
    
    def _validate_variables_exercise(self, exercise: InteractiveExercise, solution: str) -> ValidationResult:
        """Validate variables exercise."""
        if '=' not in solution:
            return ValidationResult(
                is_correct=False,
                feedback="You need to assign values to variables using the = operator.",
                suggestions=["Use variable_name = value to create variables"]
            )
        
        # Check if variables are created
        lines = solution.split('\n')
        assignments = [line for line in lines if '=' in line and not line.strip().startswith('#')]
        
        if len(assignments) == 0:
            return ValidationResult(
                is_correct=False,
                feedback="No variable assignments found.",
                suggestions=["Create at least one variable assignment"]
            )
        
        return ValidationResult(
            is_correct=True,
            feedback="Great! You've successfully created variables.",
            suggestions=["Try creating variables with different data types"]
        )
    
    def _validate_lists_exercise(self, exercise: InteractiveExercise, solution: str) -> ValidationResult:
        """Validate lists exercise."""
        if '[' not in solution or ']' not in solution:
            return ValidationResult(
                is_correct=False,
                feedback="You need to create a list using square brackets [].",
                suggestions=["Use [item1, item2, item3] to create a list"]
            )
        
        return ValidationResult(
            is_correct=True,
            feedback="Excellent! You've created a list successfully.",
            suggestions=["Try adding or removing items from your list"]
        )
    
    def _validate_functions_exercise(self, exercise: InteractiveExercise, solution: str) -> ValidationResult:
        """Validate functions exercise."""
        if 'def ' not in solution:
            return ValidationResult(
                is_correct=False,
                feedback="You need to define a function using the 'def' keyword.",
                suggestions=["Use 'def function_name():' to define a function"]
            )
        
        if ':' not in solution:
            return ValidationResult(
                is_correct=False,
                feedback="Function definitions need a colon (:) at the end.",
                suggestions=["Add a colon after the function definition line"]
            )
        
        # Check for function call
        lines = solution.split('\n')
        has_call = any(line.strip() and not line.strip().startswith('def') and 
                      not line.strip().startswith('#') and 
                      not line.strip().startswith(' ') for line in lines)
        
        if not has_call:
            return ValidationResult(
                is_correct=False,
                feedback="Don't forget to call your function after defining it.",
                suggestions=["Call your function by writing function_name()"]
            )
        
        return ValidationResult(
            is_correct=True,
            feedback="Perfect! You've defined and called a function.",
            suggestions=["Try creating functions with parameters"]
        )
    
    def _validate_loops_exercise(self, exercise: InteractiveExercise, solution: str) -> ValidationResult:
        """Validate loops exercise."""
        if 'for ' not in solution:
            return ValidationResult(
                is_correct=False,
                feedback="You need to create a for loop using the 'for' keyword.",
                suggestions=["Use 'for item in collection:' to create a loop"]
            )
        
        if ' in ' not in solution:
            return ValidationResult(
                is_correct=False,
                feedback="For loops need the 'in' keyword to iterate over a collection.",
                suggestions=["Use 'for item in list:' syntax"]
            )
        
        return ValidationResult(
            is_correct=True,
            feedback="Great job! You've created a working loop.",
            suggestions=["Try looping over different types of collections"]
        )
    
    def get_related_examples(self, topic: str, difficulty: DifficultyLevel = DifficultyLevel.BEGINNER):
        """
        Get related examples from the example repository.
        
        Args:
            topic: Topic to find examples for
            difficulty: Difficulty level filter
            
        Returns:
            List of related examples if repository is available
        """
        if self._example_repository is None:
            return []
        
        try:
            examples = self._example_repository.get_examples_by_topic(topic)
            # Filter by difficulty if needed
            filtered_examples = [
                ex for ex in examples 
                if ex.difficulty == difficulty.value
            ]
            return filtered_examples[:3]  # Limit to 3 most relevant
        except Exception:
            return []
    
    def enhance_explanation_with_examples(self, explanation: StepExplanation, topic: str) -> StepExplanation:
        """
        Enhance a step explanation with related examples from the repository.
        
        Args:
            explanation: Original explanation
            topic: Topic to find examples for
            
        Returns:
            Enhanced explanation with example references
        """
        if self._example_repository is None:
            return explanation
        
        try:
            related_examples = self.get_related_examples(topic)
            if related_examples:
                # Add example references to the explanation
                example_titles = [ex.title for ex in related_examples[:2]]
                enhanced_description = explanation.description
                if example_titles:
                    enhanced_description += f"\n\nRelated examples: {', '.join(example_titles)}"
                
                # Create enhanced explanation
                return StepExplanation(
                    step_number=explanation.step_number,
                    description=enhanced_description,
                    code_snippet=explanation.code_snippet,
                    input_example=explanation.input_example,
                    output_example=explanation.output_example,
                    related_concepts=explanation.related_concepts,
                    visual_aid=explanation.visual_aid
                )
        except Exception:
            pass
        
        return explanation