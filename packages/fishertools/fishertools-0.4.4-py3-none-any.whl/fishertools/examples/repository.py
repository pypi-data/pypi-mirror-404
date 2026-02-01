"""
Repository for managing code examples and learning scenarios.
"""

from typing import List, Optional, Dict
from .models import (
    CodeExample, Scenario, ProjectTemplate, LineByLineExplanation,
    ExampleCategory, ProjectType
)


class ExampleRepository:
    """
    Manages collections of examples and scenarios for Python beginners.
    
    Provides categorized examples with step-by-step explanations
    and simple project templates.
    """
    
    # Concept name constants
    CONCEPT_VARIABLE_ASSIGNMENT = "variable assignment"
    CONCEPT_LISTS = "lists"
    CONCEPT_LIST_METHODS = "list methods"
    CONCEPT_DICTIONARIES = "dictionaries"
    CONCEPT_FUNCTIONS = "functions"
    CONCEPT_FUNCTION_CALLS = "function calls"
    CONCEPT_LOOPS = "loops"
    CONCEPT_FOR_LOOPS = "for loops"
    CONCEPT_WHILE_LOOPS = "while loops"
    CONCEPT_CONDITIONALS = "conditionals"
    CONCEPT_USER_INPUT = "user input"
    CONCEPT_OUTPUT = "output"
    CONCEPT_ERROR_HANDLING = "error handling"
    
    # Code pattern constants
    INPUT_FUNCTION = 'input('
    
    def __init__(self, examples_dir: Optional[str] = None):
        """
        Initialize the example repository.
        
        Args:
            examples_dir: Optional directory containing example files
        """
        self.examples_dir = examples_dir
        self._examples: Dict[str, CodeExample] = {}
        self._scenarios: Dict[str, Scenario] = {}
        self._projects: Dict[str, ProjectTemplate] = {}
        self._initialize_default_examples()
        self._initialize_default_scenarios()
        self._initialize_default_projects()
    
    def get_examples_by_topic(self, topic: str) -> List[CodeExample]:
        """
        Get all examples for a specific topic.
        
        Args:
            topic: Topic name (e.g., "lists", "dictionaries", "functions")
            
        Returns:
            List[CodeExample]: Examples matching the topic
        """
        return [
            example for example in self._examples.values()
            if topic.lower() in [t.lower() for t in example.topics]
        ]
    
    def get_examples_by_category(self, category: ExampleCategory) -> List[CodeExample]:
        """
        Get all examples in a specific category.
        
        Args:
            category: Example category
            
        Returns:
            List[CodeExample]: Examples in the category
        """
        return [
            example for example in self._examples.values()
            if example.category == category
        ]
    
    def get_beginner_scenarios(self) -> List[Scenario]:
        """
        Get all scenarios suitable for beginners.
        
        Returns:
            List[Scenario]: Beginner-friendly scenarios
        """
        return [
            scenario for scenario in self._scenarios.values()
            if scenario.difficulty == "beginner"
        ]
    
    def create_simple_project(self, project_type: ProjectType) -> ProjectTemplate:
        """
        Create a simple project template with step-by-step instructions.
        
        Args:
            project_type: Type of project to create
            
        Returns:
            ProjectTemplate: Project template with instructions
        """
        project_id = f"{project_type.value}_project"
        if project_id in self._projects:
            return self._projects[project_id]
        
        # If project doesn't exist, create a basic template
        from .models import ProjectStep
        
        basic_step = ProjectStep(
            step_number=1,
            title=f"Create {project_type.value}",
            description=f"Basic {project_type.value} implementation",
            code_snippet="# Add your code here",
            explanation="This is a placeholder project template"
        )
        
        return ProjectTemplate(
            id=project_id,
            title=f"Simple {project_type.value.replace('_', ' ').title()}",
            description=f"A beginner-friendly {project_type.value} project",
            project_type=project_type,
            difficulty="beginner",
            estimated_time=30,
            steps=[basic_step],
            final_code="# Complete implementation"
        )
    
    def explain_example_line_by_line(self, example: CodeExample) -> LineByLineExplanation:
        """
        Generate line-by-line explanation for a code example.
        
        Args:
            example: Code example to explain
            
        Returns:
            LineByLineExplanation: Detailed line-by-line explanation
        """
        from .models import LineExplanation
        
        lines = example.code.strip().split('\n')
        line_explanations = []
        key_concepts = set()
        
        for i, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # Skip empty lines and comments (but still include them)
            if not stripped_line or stripped_line.startswith('#'):
                if stripped_line.startswith('#'):
                    explanation = "This is a comment that explains the code"
                    concepts = ["comments"]
                else:
                    explanation = "Empty line for readability"
                    concepts = []
            else:
                explanation, concepts = self._analyze_code_line(stripped_line)
            
            line_explanations.append(LineExplanation(
                line_number=i,
                code=line,
                explanation=explanation,
                concepts=concepts
            ))
            
            key_concepts.update(concepts)
        
        # Generate summary based on key concepts
        summary = self._generate_explanation_summary(example, list(key_concepts))
        
        return LineByLineExplanation(
            example_id=example.id,
            title=f"Line-by-line: {example.title}",
            lines=line_explanations,
            summary=summary,
            key_concepts=list(key_concepts)
        )
    
    def _analyze_code_line(self, line: str) -> tuple[str, List[str]]:
        """
        Analyze a single line of code and generate explanation.
        
        Args:
            line: Code line to analyze
            
        Returns:
            tuple: (explanation, concepts)
        """
        concepts = []
        
        # Check for variable assignment first
        if self._is_variable_assignment(line):
            return self._analyze_assignment(line)
        
        # Check for function definitions
        if line.startswith('def '):
            concepts.extend(["functions", "function definition"])
            func_name = line.split('(')[0].replace('def ', '').strip()
            return f"Defines a function named '{func_name}'", concepts
        
        # Check for function calls
        if '(' in line and ')' in line and not line.startswith('def'):
            return self._analyze_function_call(line)
        
        # Check for control structures
        control_result = self._analyze_control_structures(line)
        if control_result:
            return control_result
        
        # Check for exception handling
        exception_result = self._analyze_exception_handling(line)
        if exception_result:
            return exception_result
        
        # Check for return statements
        if line.startswith('return '):
            concepts.extend(["functions", "return statements"])
            return "Returns a value from the function", concepts
        
        # Check for import statements
        if line.startswith('import ') or line.startswith('from '):
            concepts.append("imports")
            return "Imports code from another module", concepts
        
        # Default case
        return "Executes a Python statement", []
    
    def _is_variable_assignment(self, line: str) -> bool:
        """Check if line is a variable assignment."""
        return '=' in line and not any(op in line for op in ['==', '!=', '<=', '>='])
    
    def _analyze_assignment(self, line: str) -> tuple[str, List[str]]:
        """Analyze variable assignment lines."""
        concepts = [self.CONCEPT_VARIABLE_ASSIGNMENT]
        var_name = line.split('=')[0].strip()
        
        if '[' in line and ']' in line:
            concepts.append("lists")
            if self._is_list_indexing(line):
                concepts.extend(["indexing", "list access"])
                return f"Accesses an element from a list using indexing and assigns it to '{var_name}'", concepts
            else:
                return f"Creates a list and assigns it to variable '{var_name}'", concepts
        
        if '{' in line and '}' in line:
            concepts.append("dictionaries")
            return f"Creates a dictionary and assigns it to variable '{var_name}'", concepts
        
        if self.INPUT_FUNCTION in line:
            concepts.append(self.CONCEPT_USER_INPUT)
            return f"Gets input from user and stores it in variable '{var_name}'", concepts
        
        if '(' in line and ')' in line:
            concepts.append(self.CONCEPT_FUNCTION_CALLS)
            return f"Calls a function and assigns the result to '{var_name}'", concepts
        
        return f"Assigns a value to variable '{var_name}'", concepts
    
    def _is_list_indexing(self, line: str) -> bool:
        """Check if line contains list indexing rather than list creation."""
        return line.count('[') == 1 and line.count(']') == 1 and not line.endswith(']')
    
    def _analyze_function_call(self, line: str) -> tuple[str, List[str]]:
        """Analyze function call lines."""
        concepts = [self.CONCEPT_FUNCTION_CALLS]
        
        if 'print(' in line:
            concepts.append("output")
            return "Prints output to the console", concepts
        
        if self.INPUT_FUNCTION in line:
            concepts.append(self.CONCEPT_USER_INPUT)
            return "Gets input from the user", concepts
        
        if '.append(' in line:
            concepts.extend([self.CONCEPT_LISTS, self.CONCEPT_LIST_METHODS])
            return "Adds an item to the end of a list", concepts
        
        if '.extend(' in line:
            concepts.extend([self.CONCEPT_LISTS, self.CONCEPT_LIST_METHODS])
            return "Adds multiple items to the end of a list", concepts
        
        if '.get(' in line:
            concepts.extend(["dictionaries", "dict methods"])
            return "Safely gets a value from a dictionary", concepts
        
        if any(func in line for func in ['int(', 'float(', 'str(']):
            concepts.append("type conversion")
            return "Converts a value to a different data type", concepts
        
        return "Calls a function to perform an operation", concepts
    
    def _analyze_control_structures(self, line: str) -> tuple[str, List[str]] | None:
        """Analyze control structure lines."""
        if line.startswith('if '):
            return "Checks a condition and executes code if it's true", ["conditionals", "if statements"]
        
        if line.startswith('elif '):
            return "Checks an alternative condition", ["conditionals", "elif statements"]
        
        if line.startswith('else:'):
            return "Executes when no previous conditions were true", ["conditionals", "else statements"]
        
        if line.startswith('while '):
            return "Repeats code while a condition is true", [self.CONCEPT_LOOPS, self.CONCEPT_WHILE_LOOPS]
        
        if line.startswith('for '):
            return "Repeats code for each item in a sequence", [self.CONCEPT_LOOPS, self.CONCEPT_FOR_LOOPS]
        
        return None
    
    def _analyze_exception_handling(self, line: str) -> tuple[str, List[str]] | None:
        """Analyze exception handling lines."""
        if line.startswith('try:'):
            return "Starts a block that might cause an error", [self.CONCEPT_ERROR_HANDLING, "try-except"]
        
        if line.startswith('except'):
            return "Handles errors that occur in the try block", [self.CONCEPT_ERROR_HANDLING, "try-except"]
        
        return None
    
    def _analyze_line_detailed(self, line: str) -> tuple[str, List[str]]:
        """
        Analyze a single line of code and generate detailed explanation.
        
        Args:
            line: Code line to analyze
            
        Returns:
            tuple: (explanation, concepts)
        """
        # Check variable assignment first
        if self._is_variable_assignment_detailed(line):
            return self._analyze_assignment_detailed(line)
        
        # Check function definitions
        if line.startswith('def '):
            return self._analyze_function_definition(line)
        
        # Check function calls
        if '(' in line and ')' in line and not line.startswith('def'):
            return self._analyze_function_call_detailed(line)
        
        # Check control structures
        if self._is_control_structure(line):
            return self._analyze_control_structure_detailed(line)
        
        # Check exception handling
        if self._is_exception_handling(line):
            return self._analyze_exception_detailed(line)
        
        # Check return statements
        if line.startswith('return '):
            return "Returns a value from the function", [self.CONCEPT_FUNCTIONS, "return statements"]
        
        # Check import statements
        if line.startswith('import ') or line.startswith('from '):
            return "Imports code from another module", ["imports"]
        
        # Default case
        return "Executes a Python statement", []
    
    def _is_variable_assignment_detailed(self, line: str) -> bool:
        """Check if line is a variable assignment."""
        return ('=' in line and 
                not any(op in line for op in ['==', '!=', '<=', '>=']) and
                line.count('=') == 1)
    
    def _analyze_assignment_detailed(self, line: str) -> tuple[str, List[str]]:
        """Analyze variable assignment lines with detailed logic."""
        concepts = [self.CONCEPT_VARIABLE_ASSIGNMENT]
        var_name = line.split('=')[0].strip()
        
        if '[' in line and ']' in line:
            concepts.append(self.CONCEPT_LISTS)
            if self._is_list_indexing(line):
                concepts.extend(["indexing", "list access"])
                explanation = f"Accesses an element from a list using indexing and assigns it to '{var_name}'"
            else:
                explanation = f"Creates a list and assigns it to variable '{var_name}'"
        elif '{' in line and '}' in line:
            concepts.append(self.CONCEPT_DICTIONARIES)
            explanation = f"Creates a dictionary and assigns it to variable '{var_name}'"
        elif self.INPUT_FUNCTION in line:
            concepts.append(self.CONCEPT_USER_INPUT)
            explanation = f"Gets input from user and stores it in variable '{var_name}'"
        elif '(' in line and ')' in line:
            concepts.append(self.CONCEPT_FUNCTION_CALLS)
            explanation = f"Calls a function and assigns the result to '{var_name}'"
        else:
            explanation = f"Assigns a value to variable '{var_name}'"
        
        return explanation, concepts
    
    def _analyze_function_definition(self, line: str) -> tuple[str, List[str]]:
        """Analyze function definition lines."""
        concepts = [self.CONCEPT_FUNCTIONS, "function definition"]
        func_name = line.split('(')[0].replace('def ', '').strip()
        explanation = f"Defines a function named '{func_name}'"
        return explanation, concepts
    
    def _analyze_function_call_detailed(self, line: str) -> tuple[str, List[str]]:
        """Analyze function call lines with detailed logic."""
        concepts = [self.CONCEPT_FUNCTION_CALLS]
        
        if 'print(' in line:
            concepts.append(self.CONCEPT_OUTPUT)
            explanation = "Prints output to the console"
        elif self.INPUT_FUNCTION in line:
            concepts.append(self.CONCEPT_USER_INPUT)
            explanation = "Gets input from the user"
        elif '.append(' in line:
            concepts.extend([self.CONCEPT_LISTS, self.CONCEPT_LIST_METHODS])
            explanation = "Adds an item to the end of a list"
        elif '.extend(' in line:
            concepts.extend([self.CONCEPT_LISTS, self.CONCEPT_LIST_METHODS])
            explanation = "Adds multiple items to the end of a list"
        elif '.get(' in line:
            concepts.extend([self.CONCEPT_DICTIONARIES, "dict methods"])
            explanation = "Safely gets a value from a dictionary"
        elif any(func in line for func in ['int(', 'float(', 'str(']):
            concepts.append("type conversion")
            explanation = "Converts a value to a different data type"
        else:
            explanation = "Calls a function to perform an operation"
        
        return explanation, concepts
    
    def _is_control_structure(self, line: str) -> bool:
        """Check if line is a control structure."""
        return any(line.startswith(keyword) for keyword in 
                  ['if ', 'elif ', 'else:', 'while ', 'for '])
    
    def _analyze_control_structure_detailed(self, line: str) -> tuple[str, List[str]]:
        """Analyze control structure lines."""
        if line.startswith('if '):
            return "Checks a condition and executes code if it's true", [self.CONCEPT_CONDITIONALS, "if statements"]
        elif line.startswith('elif '):
            return "Checks an alternative condition", [self.CONCEPT_CONDITIONALS, "elif statements"]
        elif line.startswith('else:'):
            return "Executes when no previous conditions were true", [self.CONCEPT_CONDITIONALS, "else statements"]
        elif line.startswith('while '):
            return "Repeats code while a condition is true", [self.CONCEPT_LOOPS, self.CONCEPT_WHILE_LOOPS]
        elif line.startswith('for '):
            return "Repeats code for each item in a sequence", [self.CONCEPT_LOOPS, self.CONCEPT_FOR_LOOPS]
        
        return "Control structure", []
    
    def _is_exception_handling(self, line: str) -> bool:
        """Check if line is exception handling."""
        return line.startswith('try:') or line.startswith('except')
    
    def _analyze_exception_detailed(self, line: str) -> tuple[str, List[str]]:
        """Analyze exception handling lines."""
        if line.startswith('try:'):
            return "Starts a block that might cause an error", [self.CONCEPT_ERROR_HANDLING, "try-except"]
        elif line.startswith('except'):
            return "Handles errors that occur in the try block", [self.CONCEPT_ERROR_HANDLING, "try-except"]
        
        return "Exception handling", [self.CONCEPT_ERROR_HANDLING]
    
    def _generate_explanation_summary(self, example: CodeExample, key_concepts: List[str]) -> str:
        """
        Generate a summary of the code explanation.
        
        Args:
            example: The code example
            key_concepts: List of key concepts found in the code
            
        Returns:
            str: Summary explanation
        """
        concept_descriptions = {
            self.CONCEPT_VARIABLE_ASSIGNMENT: "storing values in variables",
            self.CONCEPT_LISTS: "working with ordered collections",
            self.CONCEPT_DICTIONARIES: "using key-value data structures",
            self.CONCEPT_FUNCTIONS: "defining and calling reusable code blocks",
            "conditionals": "making decisions with if/else statements",
            "loops": "repeating code execution",
            self.CONCEPT_USER_INPUT: "getting data from users",
            self.CONCEPT_ERROR_HANDLING: "managing potential errors gracefully",
            self.CONCEPT_OUTPUT: "displaying results to users"
        }
        
        if not key_concepts:
            return f"This example demonstrates basic Python syntax: {example.description}"
        
        # Get descriptions for found concepts
        found_descriptions = []
        for concept in key_concepts:
            if concept in concept_descriptions:
                found_descriptions.append(concept_descriptions[concept])
        
        if found_descriptions:
            concepts_text = ", ".join(found_descriptions[:-1])
            if len(found_descriptions) > 1:
                concepts_text += f", and {found_descriptions[-1]}"
            else:
                concepts_text = found_descriptions[0]
            
            return f"This example demonstrates {concepts_text}. {example.description}"
        else:
            return f"This example shows various Python programming concepts. {example.description}"
    
    def break_down_complex_concept(self, concept: str, context: str = "") -> List[str]:
        """
        Break down complex programming concepts into simple steps.
        
        Args:
            concept: The complex concept to break down
            context: Additional context about how the concept is used
            
        Returns:
            List[str]: List of simple explanation steps
        """
        concept_breakdowns = {
            "list comprehension": [
                "List comprehension is a concise way to create lists",
                "It follows the pattern: [expression for item in iterable]",
                "The expression is applied to each item in the iterable",
                "The results are collected into a new list",
                "It's equivalent to using a for loop but more compact"
            ],
            
            "dictionary comprehension": [
                "Dictionary comprehension creates dictionaries in one line",
                "It follows the pattern: {key: value for item in iterable}",
                "Each item in the iterable generates a key-value pair",
                "The result is a new dictionary with all the pairs",
                "It's more efficient than using loops to build dictionaries"
            ],
            
            "exception handling": [
                "Exception handling prevents programs from crashing",
                "Use 'try:' to mark code that might cause an error",
                "Use 'except:' to specify what to do if an error occurs",
                "The program continues running after handling the error",
                "Always handle specific exceptions when possible"
            ],
            
            "function parameters": [
                "Functions can accept input values called parameters",
                "Parameters are defined in parentheses after the function name",
                "When calling the function, you provide arguments for each parameter",
                "The function uses these values to perform its task",
                "Parameters make functions flexible and reusable"
            ],
            
            "loops with conditions": [
                "Loops can include conditions to control execution",
                "Use 'if' statements inside loops to check conditions",
                "Use 'continue' to skip the rest of the current iteration",
                "Use 'break' to exit the loop completely",
                "This allows for more complex loop behavior"
            ],
            
            "nested data structures": [
                "Data structures can contain other data structures",
                "Lists can contain other lists (nested lists)",
                "Dictionaries can contain lists or other dictionaries",
                "Access nested elements using multiple brackets or keys",
                "This allows for organizing complex data hierarchically"
            ]
        }
        
        # Return breakdown if available, otherwise create a generic one
        if concept.lower() in concept_breakdowns:
            return concept_breakdowns[concept.lower()]
        
        # Generic breakdown for unknown concepts
        return [
            f"The concept '{concept}' is an important programming idea",
            f"It helps solve specific problems in your code",
            f"Understanding {concept} will make you a better programmer",
            f"Practice using {concept} in different situations",
            f"Look for examples of {concept} in real code"
        ]
    
    def get_concept_prerequisites(self, concept: str) -> List[str]:
        """
        Get the prerequisites needed to understand a concept.
        
        Args:
            concept: The concept to check prerequisites for
            
        Returns:
            List[str]: List of prerequisite concepts
        """
        prerequisites_map = {
            "list comprehension": [self.CONCEPT_LISTS, self.CONCEPT_FOR_LOOPS, "expressions"],
            "dictionary comprehension": [self.CONCEPT_DICTIONARIES, self.CONCEPT_FOR_LOOPS, "key-value pairs"],
            "exception handling": [self.CONCEPT_FUNCTIONS, "conditionals"],
            "nested loops": [self.CONCEPT_FOR_LOOPS, self.CONCEPT_WHILE_LOOPS, "indentation"],
            "function parameters": [self.CONCEPT_FUNCTIONS, "variables"],
            "lambda functions": [self.CONCEPT_FUNCTIONS, "expressions"],
            "file operations": ["strings", "exception handling"],
            "class methods": ["classes", "functions", "self parameter"]
        }
        
        return prerequisites_map.get(concept.lower(), [])
    
    def add_example(self, example: CodeExample) -> None:
        """
        Add a new example to the repository.
        
        Args:
            example: Code example to add
        """
        self._examples[example.id] = example
    
    def search_examples(self, query: str, category: Optional[ExampleCategory] = None) -> List[CodeExample]:
        """
        Search for examples matching a query.
        
        Args:
            query: Search query
            category: Optional category filter
            
        Returns:
            List[CodeExample]: Matching examples
        """
        query_lower = query.lower()
        results = []
        
        for example in self._examples.values():
            # Filter by category if specified
            if category and example.category != category:
                continue
                
            # Search in title, description, topics, and code
            if (query_lower in example.title.lower() or
                query_lower in example.description.lower() or
                any(query_lower in topic.lower() for topic in example.topics) or
                query_lower in example.code.lower() or
                # Handle plural/singular variations
                (query_lower.endswith('s') and query_lower[:-1] in example.title.lower()) or
                (query_lower.endswith('s') and any(query_lower[:-1] in topic.lower() for topic in example.topics)) or
                (not query_lower.endswith('s') and (query_lower + 's') in example.title.lower()) or
                (not query_lower.endswith('s') and any((query_lower + 's') in topic.lower() for topic in example.topics))):
                results.append(example)
        
        return results
    
    def _initialize_default_examples(self) -> None:
        """Initialize repository with default examples for beginners."""
        from .models import ProjectStep
        
        # List examples
        list_examples = [
            CodeExample(
                id="list_basics",
                title="Working with Lists - Basics",
                description="Learn how to create, access, and modify lists",
                code="""# Creating lists
fruits = ['apple', 'banana', 'orange']
numbers = [1, 2, 3, 4, 5]

# Accessing elements
first_fruit = fruits[0]  # 'apple'
last_number = numbers[-1]  # 5

# Adding elements
fruits.append('grape')
numbers.extend([6, 7])

# Modifying elements
fruits[1] = 'blueberry'

print(f"Fruits: {fruits}")
print(f"Numbers: {numbers}")""",
                explanation="Lists are ordered collections that can store multiple items. You can access items by index, add new items, and modify existing ones.",
                difficulty="beginner",
                topics=["lists", "indexing", "append", "extend"],
                prerequisites=[],
                category=ExampleCategory.COLLECTIONS,
                expected_output="Fruits: ['apple', 'blueberry', 'orange', 'grape']\nNumbers: [1, 2, 3, 4, 5, 6, 7]",
                common_mistakes=["Using 1-based indexing instead of 0-based", "Forgetting that negative indices count from the end"]
            ),
            
            CodeExample(
                id="list_operations",
                title="List Operations and Methods",
                description="Common list operations like sorting, searching, and removing items",
                code="""# Sample list
numbers = [3, 1, 4, 1, 5, 9, 2, 6]

# Sorting
sorted_numbers = sorted(numbers)  # Creates new list
numbers.sort()  # Modifies original list

# Searching
if 5 in numbers:
    position = numbers.index(5)
    print(f"Found 5 at position {position}")

# Removing items
numbers.remove(1)  # Removes first occurrence
last_item = numbers.pop()  # Removes and returns last item

# List comprehension
squares = [x**2 for x in range(1, 6)]

print(f"Sorted: {sorted_numbers}")
print(f"Modified: {numbers}")
print(f"Squares: {squares}")""",
                explanation="Lists have many built-in methods for common operations. Understanding the difference between methods that modify the list and those that return new lists is important.",
                difficulty="beginner",
                topics=["lists", "sorting", "searching", "list comprehension"],
                prerequisites=["list_basics"],
                category=ExampleCategory.COLLECTIONS,
                expected_output="Found 5 at position 4\nSorted: [1, 1, 2, 3, 4, 5, 6, 9]\nModified: [1, 2, 3, 4, 5, 9]\nSquares: [1, 4, 9, 16, 25]",
                common_mistakes=["Confusing sort() and sorted()", "Using remove() when item might not exist"]
            )
        ]
        
        # Dictionary examples
        dict_examples = [
            CodeExample(
                id="dict_basics",
                title="Working with Dictionaries - Basics",
                description="Learn how to create, access, and modify dictionaries",
                code="""# Creating dictionaries
student = {
    'name': 'Alice',
    'age': 20,
    'grade': 'A',
    'courses': ['Math', 'Physics']
}

# Accessing values
name = student['name']
age = student.get('age', 0)  # Safe access with default

# Adding/modifying values
student['email'] = 'alice@example.com'
student['age'] = 21

# Checking if key exists
if 'grade' in student:
    print(f"{name} has grade: {student['grade']}")

# Getting all keys, values, items
print(f"Keys: {list(student.keys())}")
print(f"Values: {list(student.values())}")""",
                explanation="Dictionaries store key-value pairs and provide fast lookup by key. Use get() for safe access to avoid KeyError.",
                difficulty="beginner",
                topics=["dictionaries", "dictionary", "key-value pairs", "get method"],
                prerequisites=[],
                category=ExampleCategory.COLLECTIONS,
                expected_output="Alice has grade: A\nKeys: ['name', 'age', 'grade', 'courses', 'email']\nValues: ['Alice', 21, 'A', ['Math', 'Physics'], 'alice@example.com']",
                common_mistakes=["Using [] instead of get() for optional keys", "Trying to access non-existent keys"]
            )
        ]
        
        # User input examples
        input_examples = [
            CodeExample(
                id="safe_input_basics",
                title="Safe User Input - Basics",
                description="Learn how to safely get and validate user input",
                code="""# Getting basic input
name = input("Enter your name: ").strip()

# Getting and validating numeric input
while True:
    try:
        age = int(input("Enter your age: "))
        if age < 0:
            print("Age cannot be negative. Please try again.")
            continue
        break
    except ValueError:
        print("Please enter a valid number.")

# Getting yes/no input
while True:
    choice = input("Do you want to continue? (y/n): ").lower().strip()
    if choice in ['y', 'yes']:
        print("Continuing...")
        break
    elif choice in ['n', 'no']:
        print("Stopping...")
        break
    else:
        print("Please enter 'y' or 'n'.")

print(f"Hello {name}, you are {age} years old.")""",
                explanation="Always validate user input to prevent errors. Use try-except for type conversion and loops for validation.",
                difficulty="beginner",
                topics=["input", "validation", "try-except", "loops"],
                prerequisites=[],
                category=ExampleCategory.USER_INPUT,
                expected_output="# Output depends on user input",
                common_mistakes=["Not validating input", "Not handling ValueError", "Not stripping whitespace"]
            )
        ]
        
        # Add all examples to repository
        for example in list_examples + dict_examples + input_examples:
            self._examples[example.id] = example
    
    def _initialize_default_scenarios(self) -> None:
        """Initialize repository with default learning scenarios."""
        # Collections scenario
        collections_scenario = Scenario(
            id="collections_basics",
            title="Python Collections Fundamentals",
            description="Learn the basics of working with lists and dictionaries",
            examples=[self._examples["list_basics"], self._examples["dict_basics"]],
            learning_objectives=[
                "Understand how to create and use lists",
                "Learn dictionary key-value operations",
                "Practice safe data access patterns"
            ],
            difficulty="beginner",
            estimated_time=45
        )
        
        self._scenarios[collections_scenario.id] = collections_scenario
    
    def _initialize_default_projects(self) -> None:
        """Initialize repository with default project templates."""
        from .models import ProjectStep
        
        # Calculator project
        calculator_steps = [
            ProjectStep(
                step_number=1,
                title="Create basic calculator functions",
                description="Define functions for basic arithmetic operations",
                code_snippet="""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b""",
                explanation="Start by creating simple functions for each operation. Notice the error handling for division by zero.",
                hints=["Remember to handle division by zero", "Keep functions simple and focused"]
            ),
            
            ProjectStep(
                step_number=2,
                title="Create the main calculator loop",
                description="Build the user interface and input handling",
                code_snippet="""def calculator():
    print("Simple Calculator")
    print("Operations: +, -, *, /")
    print("Type 'quit' to exit")
    
    while True:
        try:
            # Get first number
            first = input("Enter first number (or 'quit'): ")
            if first.lower() == 'quit':
                break
            first = float(first)
            
            # Get operation
            operation = input("Enter operation (+, -, *, /): ")
            if operation not in ['+', '-', '*', '/']:
                print("Invalid operation!")
                continue
            
            # Get second number
            second = float(input("Enter second number: "))
            
            # Calculate result
            if operation == '+':
                result = add(first, second)
            elif operation == '-':
                result = subtract(first, second)
            elif operation == '*':
                result = multiply(first, second)
            elif operation == '/':
                result = divide(first, second)
            
            print(f"Result: {result}")
            
        except ValueError:
            print("Please enter valid numbers!")

# Run the calculator
calculator()""",
                explanation="The main loop handles user input, validates operations, and calls the appropriate function.",
                hints=["Use try-except for input validation", "Provide clear error messages", "Allow users to exit gracefully"]
            )
        ]
        
        calculator_project = ProjectTemplate(
            id="calculator_project",
            title="Simple Calculator",
            description="Build a basic calculator that performs arithmetic operations",
            project_type=ProjectType.CALCULATOR,
            difficulty="beginner",
            estimated_time=60,
            steps=calculator_steps,
            final_code="""def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b

def calculator():
    print("Simple Calculator")
    print("Operations: +, -, *, /")
    print("Type 'quit' to exit")
    
    while True:
        try:
            first = input("Enter first number (or 'quit'): ")
            if first.lower() == 'quit':
                break
            first = float(first)
            
            operation = input("Enter operation (+, -, *, /): ")
            if operation not in ['+', '-', '*', '/']:
                print("Invalid operation!")
                continue
            
            second = float(input("Enter second number: "))
            
            if operation == '+':
                result = add(first, second)
            elif operation == '-':
                result = subtract(first, second)
            elif operation == '*':
                result = multiply(first, second)
            elif operation == '/':
                result = divide(first, second)
            
            print(f"Result: {result}")
            
        except ValueError:
            print("Please enter valid numbers!")

if __name__ == "__main__":
    calculator()""",
            extensions=[
                "Add more operations (power, square root, etc.)",
                "Add memory functions (store/recall)",
                "Create a GUI version using tkinter",
                "Add calculation history"
            ]
        )
        
        self._projects[calculator_project.id] = calculator_project