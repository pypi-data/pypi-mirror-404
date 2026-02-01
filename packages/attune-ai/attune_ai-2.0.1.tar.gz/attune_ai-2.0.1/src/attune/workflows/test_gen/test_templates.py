"""Test Template Generation.

Functions to generate pytest test code for functions and classes.

Copyright 2025 Smart-AI-Memory
Licensed under Fair Source License 0.9
"""



def generate_test_for_function(module: str, func: dict) -> str:
    """Generate executable tests for a function based on AST analysis."""
    name = func["name"]
    params = func.get("params") or []  # List of (name, type, default) tuples, handle None
    param_names = func.get("param_names") or [p[0] if isinstance(p, tuple) else p for p in params]
    is_async = func.get("is_async", False)
    return_type = func.get("return_type")
    raises = func.get("raises") or []
    has_side_effects = func.get("has_side_effects", False)

    # Generate test values based on parameter types
    test_cases = generate_test_cases_for_params(params)
    param_str = ", ".join(test_cases.get("valid_args", [""] * len(params)))

    # Build parametrized test if we have multiple test cases
    parametrize_cases = test_cases.get("parametrize_cases", [])

    tests = []
    tests.append(f"import pytest\nfrom {module} import {name}\n")

    # Generate parametrized test if we have cases
    if parametrize_cases and len(parametrize_cases) > 1:
        param_names_str = ", ".join(param_names) if param_names else "value"
        cases_str = ",\n    ".join(parametrize_cases)

        if is_async:
            tests.append(
                f'''
@pytest.mark.parametrize("{param_names_str}", [
    {cases_str},
])
@pytest.mark.asyncio
async def test_{name}_with_various_inputs({param_names_str}):
    """Test {name} with various input combinations."""
    result = await {name}({", ".join(param_names)})
    assert result is not None
''',
            )
        else:
            tests.append(
                f'''
@pytest.mark.parametrize("{param_names_str}", [
    {cases_str},
])
def test_{name}_with_various_inputs({param_names_str}):
    """Test {name} with various input combinations."""
    result = {name}({", ".join(param_names)})
    assert result is not None
''',
            )
    # Simple valid input test
    elif is_async:
        tests.append(
            f'''
@pytest.mark.asyncio
async def test_{name}_returns_value():
    """Test that {name} returns a value with valid inputs."""
    result = await {name}({param_str})
    assert result is not None
''',
        )
    else:
        tests.append(
            f'''
def test_{name}_returns_value():
    """Test that {name} returns a value with valid inputs."""
    result = {name}({param_str})
    assert result is not None
''',
        )

    # Generate edge case tests based on parameter types
    edge_cases = test_cases.get("edge_cases", [])
    if edge_cases:
        edge_cases_str = ",\n    ".join(edge_cases)
        if is_async:
            tests.append(
                f'''
@pytest.mark.parametrize("edge_input", [
    {edge_cases_str},
])
@pytest.mark.asyncio
async def test_{name}_edge_cases(edge_input):
    """Test {name} with edge case inputs."""
    try:
        result = await {name}(edge_input)
        # Function should either return a value or raise an expected error
        assert result is not None or result == 0 or result == "" or result == []
    except (ValueError, TypeError, KeyError) as e:
        # Expected error for edge cases
        assert str(e)  # Error message should not be empty
''',
            )
        else:
            tests.append(
                f'''
@pytest.mark.parametrize("edge_input", [
    {edge_cases_str},
])
def test_{name}_edge_cases(edge_input):
    """Test {name} with edge case inputs."""
    try:
        result = {name}(edge_input)
        # Function should either return a value or raise an expected error
        assert result is not None or result == 0 or result == "" or result == []
    except (ValueError, TypeError, KeyError) as e:
        # Expected error for edge cases
        assert str(e)  # Error message should not be empty
''',
            )

    # Generate exception tests for each raised exception
    for exc_type in raises[:3]:  # Limit to 3 exception types
        if is_async:
            tests.append(
                f'''
@pytest.mark.asyncio
async def test_{name}_raises_{exc_type.lower()}():
    """Test that {name} raises {exc_type} for invalid inputs."""
    with pytest.raises({exc_type}):
        await {name}(None)  # Adjust input to trigger {exc_type}
''',
            )
        else:
            tests.append(
                f'''
def test_{name}_raises_{exc_type.lower()}():
    """Test that {name} raises {exc_type} for invalid inputs."""
    with pytest.raises({exc_type}):
        {name}(None)  # Adjust input to trigger {exc_type}
''',
            )

    # Add return type assertion if we know the type
    if return_type and return_type not in ("None", "Any"):
        type_check = get_type_assertion(return_type)
        if type_check and not has_side_effects:
            if is_async:
                tests.append(
                    f'''
@pytest.mark.asyncio
async def test_{name}_returns_correct_type():
    """Test that {name} returns the expected type."""
    result = await {name}({param_str})
    {type_check}
''',
                )
            else:
                tests.append(
                    f'''
def test_{name}_returns_correct_type():
    """Test that {name} returns the expected type."""
    result = {name}({param_str})
    {type_check}
''',
                )

    return "\n".join(tests)


def generate_test_cases_for_params(params: list) -> dict:
    """Generate test cases based on parameter types."""
    valid_args = []
    parametrize_cases = []
    edge_cases = []

    for param in params:
        if isinstance(param, tuple) and len(param) >= 2:
            _name, type_hint, default = param[0], param[1], param[2] if len(param) > 2 else None
        else:
            _name = param if isinstance(param, str) else str(param)
            type_hint = "Any"
            default = None

        # Generate valid value based on type
        if "str" in type_hint.lower():
            valid_args.append('"test_value"')
            parametrize_cases.extend(['"hello"', '"world"', '"test_string"'])
            edge_cases.extend(['""', '" "', '"a" * 1000'])
        elif "int" in type_hint.lower():
            valid_args.append("42")
            parametrize_cases.extend(["0", "1", "100", "-1"])
            edge_cases.extend(["0", "-1", "2**31 - 1"])
        elif "float" in type_hint.lower():
            valid_args.append("3.14")
            parametrize_cases.extend(["0.0", "1.0", "-1.5", "100.5"])
            edge_cases.extend(["0.0", "-0.0", "float('inf')"])
        elif "bool" in type_hint.lower():
            valid_args.append("True")
            parametrize_cases.extend(["True", "False"])
        elif "list" in type_hint.lower():
            valid_args.append("[1, 2, 3]")
            parametrize_cases.extend(["[]", "[1]", "[1, 2, 3]"])
            edge_cases.extend(["[]", "[None]"])
        elif "dict" in type_hint.lower():
            valid_args.append('{"key": "value"}')
            parametrize_cases.extend(["{}", '{"a": 1}', '{"key": "value"}'])
            edge_cases.extend(["{}"])
        elif default is not None:
            valid_args.append(str(default))
        else:
            valid_args.append("None")
            edge_cases.append("None")

    return {
        "valid_args": valid_args,
        "parametrize_cases": parametrize_cases[:5],  # Limit cases
        "edge_cases": list(dict.fromkeys(edge_cases))[
            :5
        ],  # Unique edge cases (preserves order)
    }


def get_type_assertion(return_type: str) -> str | None:
    """Generate assertion for return type checking."""
    type_map = {
        "str": "assert isinstance(result, str)",
        "int": "assert isinstance(result, int)",
        "float": "assert isinstance(result, (int, float))",
        "bool": "assert isinstance(result, bool)",
        "list": "assert isinstance(result, list)",
        "dict": "assert isinstance(result, dict)",
        "tuple": "assert isinstance(result, tuple)",
    }
    for type_name, assertion in type_map.items():
        if type_name in return_type.lower():
            return assertion
    return None


def get_param_test_values(type_hint: str) -> list[str]:
    """Get test values for a single parameter based on its type."""
    type_hint_lower = type_hint.lower()
    if "str" in type_hint_lower:
        return ['"hello"', '"world"', '"test_string"']
    if "int" in type_hint_lower:
        return ["0", "1", "42", "-1"]
    if "float" in type_hint_lower:
        return ["0.0", "1.0", "3.14"]
    if "bool" in type_hint_lower:
        return ["True", "False"]
    if "list" in type_hint_lower:
        return ["[]", "[1, 2, 3]"]
    if "dict" in type_hint_lower:
        return ["{}", '{"key": "value"}']
    return ['"test_value"']


def generate_test_for_class(module: str, cls: dict) -> str:
    """Generate executable test class based on AST analysis."""
    name = cls["name"]
    init_params = cls.get("init_params", [])
    methods = cls.get("methods", [])
    required_params = cls.get("required_init_params", 0)
    _docstring = cls.get("docstring", "")  # Reserved for future use

    # Generate constructor arguments - ensure we have values for ALL required params
    init_args = generate_test_cases_for_params(init_params)
    valid_args = init_args.get("valid_args", [])

    # Ensure we have enough args for required params
    while len(valid_args) < required_params:
        valid_args.append('"test_value"')

    init_arg_str = ", ".join(valid_args)

    tests = []
    tests.append(f"import pytest\nfrom {module} import {name}\n")

    # Fixture for class instance
    tests.append(
        f'''
@pytest.fixture
def {name.lower()}_instance():
    """Create a {name} instance for testing."""
    return {name}({init_arg_str})
''',
    )

    # Test initialization
    tests.append(
        f'''
class Test{name}:
    """Tests for {name} class."""

    def test_initialization(self):
        """Test that {name} can be instantiated."""
        instance = {name}({init_arg_str})
        assert instance is not None
''',
    )

    # Only generate parametrized tests for single-param classes to avoid tuple mismatches
    if len(init_params) == 1 and init_params[0][2] is None:
        # Single required param - safe to parametrize
        param_name = init_params[0][0]
        param_type = init_params[0][1]
        cases = get_param_test_values(param_type)
        if len(cases) > 1:
            cases_str = ",\n        ".join(cases)
            tests.append(
                f'''
    @pytest.mark.parametrize("{param_name}", [
        {cases_str},
    ])
    def test_initialization_with_various_args(self, {param_name}):
        """Test {name} initialization with various arguments."""
        instance = {name}({param_name})
        assert instance is not None
''',
            )

    # Generate tests for each public method
    for method in methods[:5]:  # Limit to 5 methods
        method_name = method.get("name", "")
        if method_name.startswith("_") and method_name != "__init__":
            continue
        if method_name == "__init__":
            continue

        method_params = method.get("params", [])[1:]  # Skip self
        is_async = method.get("is_async", False)
        raises = method.get("raises", [])

        # Generate method call args
        method_args = generate_test_cases_for_params(method_params)
        method_arg_str = ", ".join(method_args.get("valid_args", []))

        if is_async:
            tests.append(
                f'''
    @pytest.mark.asyncio
    async def test_{method_name}_returns_value(self, {name.lower()}_instance):
        """Test that {method_name} returns a value."""
        result = await {name.lower()}_instance.{method_name}({method_arg_str})
        assert result is not None or result == 0 or result == "" or result == []
''',
            )
        else:
            tests.append(
                f'''
    def test_{method_name}_returns_value(self, {name.lower()}_instance):
        """Test that {method_name} returns a value."""
        result = {name.lower()}_instance.{method_name}({method_arg_str})
        assert result is not None or result == 0 or result == "" or result == []
''',
            )

        # Add exception tests for methods that raise
        for exc_type in raises[:2]:
            if is_async:
                tests.append(
                    f'''
    @pytest.mark.asyncio
    async def test_{method_name}_raises_{exc_type.lower()}(self, {name.lower()}_instance):
        """Test that {method_name} raises {exc_type} for invalid inputs."""
        with pytest.raises({exc_type}):
            await {name.lower()}_instance.{method_name}(None)
''',
                )
            else:
                tests.append(
                    f'''
    def test_{method_name}_raises_{exc_type.lower()}(self, {name.lower()}_instance):
        """Test that {method_name} raises {exc_type} for invalid inputs."""
        with pytest.raises({exc_type}):
            {name.lower()}_instance.{method_name}(None)
''',
                )

    return "\n".join(tests)
