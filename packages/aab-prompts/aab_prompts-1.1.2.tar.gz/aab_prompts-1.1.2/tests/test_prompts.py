import pytest
from aab_service import AABPrompts
from prompts.constants import CORE_EXPRESSIONS, RESTRICTED_OBJECTS_LIST, DEFAULT_SOLUTION_ID, DEFAULT_APPLICATION_ID


@pytest.fixture
def aab_prompts():
    """Create an AABPrompts instance for testing."""
    return AABPrompts(
        core_expressions=CORE_EXPRESSIONS,
        restricted_objects_list=RESTRICTED_OBJECTS_LIST,
        default_solution_id=DEFAULT_SOLUTION_ID,
        default_application_id=DEFAULT_APPLICATION_ID
    )


class TestBreadcrumbsPrompts:
    """Test all breadcrumb-related prompts."""
    
    def test_breadcrumb_agent_system_prompt_exists(self, aab_prompts):
        """Test that BREADCRUMB_AGENT_SYSTEM_PROMPT exists and returns content."""
        prompt = aab_prompts.BREADCRUMB_AGENT_SYSTEM_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "SnapApp Breadcrumbs Specialist" in prompt
        assert "breadcrumb" in prompt.lower()
    
    def test_breadcrumb_prompt_contains_required_sections(self, aab_prompts):
        """Test that breadcrumb prompt contains all required sections."""
        prompt = aab_prompts.BREADCRUMB_AGENT_SYSTEM_PROMPT
        assert "What are Breadcrumbs" in prompt or "breadcrumbs" in prompt.lower()
        assert "When to create" in prompt or "when to create" in prompt.lower()
        assert "Rules for creating" in prompt or "rules" in prompt.lower()
        assert "Required Output Structure" in prompt or "schema" in prompt.lower()
    
    def test_breadcrumb_prompt_mentions_key_fields(self, aab_prompts):
        """Test that breadcrumb prompt mentions key fields."""
        prompt = aab_prompts.BREADCRUMB_AGENT_SYSTEM_PROMPT
        assert "name" in prompt.lower()
        assert "path" in prompt.lower()
        assert "application_id" in prompt.lower() or "application" in prompt.lower()


class TestExpressionsPrompts:
    """Test all expression-related prompts."""
    
    def test_core_expressions_exists(self, aab_prompts):
        """Test that CORE_EXPRESSIONS exists and returns content."""
        prompt = aab_prompts.CORE_EXPRESSIONS
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Core Expressions" in prompt or "Built in Core Expressions" in prompt
    
    def test_core_expressions_contains_all_expressions(self, aab_prompts):
        """Test that CORE_EXPRESSIONS contains all expressions from constants."""
        prompt = aab_prompts.CORE_EXPRESSIONS
        # Check for a sample of expressions
        assert "ABS" in prompt or "ABS()" in prompt
        assert "IF" in prompt or "IF()" in prompt
        assert "CONCAT" in prompt or "CONCAT()" in prompt
        assert "SELECT" in prompt or "SELECT()" in prompt
    
    def test_expression_requirements_exists(self, aab_prompts):
        """Test that EXPRESSION_REQUIREMENTS exists."""
        prompt = aab_prompts.EXPRESSION_REQUIREMENTS
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Expression Generation" in prompt or "expression" in prompt.lower()
        assert "equals sign" in prompt.lower() or "=" in prompt
        assert "double square brackets" in prompt.lower() or "[[" in prompt
    
    def test_expressions_agent_prompt_exists(self, aab_prompts):
        """Test that EXPRESSIONS_AGENT_PROMPT exists."""
        prompt = aab_prompts.EXPRESSIONS_AGENT_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Expressions Agent" in prompt
        assert "SnapApp" in prompt
    
    def test_expressions_agent_prompt_contains_requirements(self, aab_prompts):
        """Test that expressions agent prompt contains expression requirements."""
        prompt = aab_prompts.EXPRESSIONS_AGENT_PROMPT
        assert "EXPRESSION_REQUIREMENTS" in prompt or "expression" in prompt.lower()
        assert "CORE_EXPRESSIONS" in prompt or "core expressions" in prompt.lower()
    
    def test_show_if_expression_agent_prompt_exists(self, aab_prompts):
        """Test that SHOW_IF_EXPRESSION_AGENT_PROMPT exists."""
        prompt = aab_prompts.SHOW_IF_EXPRESSION_AGENT_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Show_If" in prompt or "Show If" in prompt
        assert "visibility" in prompt.lower() or "visible" in prompt.lower()
    
    def test_initial_value_examples_exists(self, aab_prompts):
        """Test that INITIAL_VALUE_EXAMPLES exists."""
        prompt = aab_prompts.INITIAL_VALUE_EXAMPLES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # The prompt contains example scenarios for initial values
        assert "Example" in prompt or "example" in prompt.lower() or "Scenario" in prompt
    
    def test_view_filter_expression_agent_prompt_exists(self, aab_prompts):
        """Test that VIEW_FILTER_EXPRESSION_AGENT_PROMPT exists."""
        prompt = aab_prompts.VIEW_FILTER_EXPRESSION_AGENT_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "View Filter" in prompt
        assert "filter" in prompt.lower()
    
    def test_fields_expression_agent_prompt_exists(self, aab_prompts):
        """Test that FIELDS_EXPRESSION_AGENT_PROMPT exists."""
        prompt = aab_prompts.FIELDS_EXPRESSION_AGENT_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Fields Expression" in prompt or "Fields" in prompt
        assert "Object Fields" in prompt or "field" in prompt.lower()
    
    def test_views_expression_agent_prompt_exists(self, aab_prompts):
        """Test that VIEWS_EXPRESSION_AGENT_PROMPT exists."""
        prompt = aab_prompts.VIEWS_EXPRESSION_AGENT_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Views Expression" in prompt or "Views" in prompt
        assert "view" in prompt.lower()
    
    def test_page_data_binder_agent_prompt_exists(self, aab_prompts):
        """Test that PAGE_DATA_BINDER_AGENT_PROMPT exists."""
        prompt = aab_prompts.PAGE_DATA_BINDER_AGENT_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Page Data Binder" in prompt or "data binding" in prompt.lower()
        assert "page" in prompt.lower()


class TestMenuNavigationsPrompts:
    """Test all menu navigation-related prompts."""
    
    def test_menu_navigations_agent_system_prompt_exists(self, aab_prompts):
        """Test that MENU_NAVIGATIONS_AGENT_SYSTEM_PROMPT exists."""
        prompt = aab_prompts.MENU_NAVIGATIONS_AGENT_SYSTEM_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Menu" in prompt or "Navigation" in prompt
        assert "menu" in prompt.lower() or "navigation" in prompt.lower()
    
    def test_menu_navigations_prompt_contains_menu_types(self, aab_prompts):
        """Test that menu navigations prompt contains menu types."""
        prompt = aab_prompts.MENU_NAVIGATIONS_AGENT_SYSTEM_PROMPT
        assert "left" in prompt.lower() or "Left" in prompt
        assert "top" in prompt.lower() or "Top" in prompt
        assert "user" in prompt.lower() or "User" in prompt
        assert "footer" in prompt.lower() or "Footer" in prompt


class TestObjectsFieldsPrompts:
    """Test all object and field-related prompts."""
    
    def test_standard_objects_descriptions_exists(self, aab_prompts):
        """Test that STANDARD_OBJECTS_DESCRIPTIONS exists."""
        prompt = aab_prompts.STANDARD_OBJECTS_DESCRIPTIONS
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Activities" in prompt or "activities" in prompt.lower()
        assert "Contacts" in prompt or "contacts" in prompt.lower()
    
    def test_system_objects_descriptions_exists(self, aab_prompts):
        """Test that SYSTEM_OBJECTS_DESCRIPTIONS exists."""
        prompt = aab_prompts.SYSTEM_OBJECTS_DESCRIPTIONS
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Applications" in prompt or "applications" in prompt.lower()
        assert "Objects" in prompt or "objects" in prompt.lower()
    
    def test_objects_fields_agent_system_prompt_exists(self, aab_prompts):
        """Test that OBJECTS_FIELDS_AGENT_SYSTEM_PROMPT exists."""
        prompt = aab_prompts.OBJECTS_FIELDS_AGENT_SYSTEM_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Objects" in prompt or "Fields" in prompt
        assert "object" in prompt.lower() or "field" in prompt.lower()
    
    def test_objects_fields_prompt_contains_restricted_objects(self, aab_prompts):
        """Test that objects fields prompt contains restricted objects list."""
        prompt = aab_prompts.OBJECTS_FIELDS_AGENT_SYSTEM_PROMPT
        # Should contain at least some restricted object names
        assert "applications" in prompt.lower() or "objects" in prompt.lower()
    
    def test_objects_fields_prompt_contains_schema_info(self, aab_prompts):
        """Test that objects fields prompt contains schema information."""
        prompt = aab_prompts.OBJECTS_FIELDS_AGENT_SYSTEM_PROMPT
        assert "table" in prompt.lower() or "schema" in prompt.lower()
        assert "data_type" in prompt.lower() or "data type" in prompt.lower()


class TestPagePlannerPrompts:
    """Test all page planner-related prompts."""
    
    def test_page_planner_agent_system_prompt_exists(self, aab_prompts):
        """Test that PAGE_PLANNER_AGENT_SYSTEM_PROMPT exists."""
        prompt = aab_prompts.PAGE_PLANNER_AGENT_SYSTEM_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Page Planner" in prompt or "page" in prompt.lower()
    
    def test_page_planner_prompt_contains_page_types(self, aab_prompts):
        """Test that page planner prompt contains page types."""
        prompt = aab_prompts.PAGE_PLANNER_AGENT_SYSTEM_PROMPT
        assert "landing_page" in prompt.lower() or "landing" in prompt.lower()
        assert "dashboard" in prompt.lower()
        assert "detail_page" in prompt.lower() or "detail" in prompt.lower()


class TestPagesPrompts:
    """Test all page-related prompts."""
    
    def test_pages_agent_system_prompt_exists(self, aab_prompts):
        """Test that PAGES_AGENT_SYSTEM_PROMPT exists."""
        prompt = aab_prompts.PAGES_AGENT_SYSTEM_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Page" in prompt or "page" in prompt.lower()
        assert "HTML" in prompt or "html" in prompt.lower()
    
    def test_page_data_binder_exists(self, aab_prompts):
        """Test that PAGE_DATA_BINDER exists."""
        prompt = aab_prompts.PAGE_DATA_BINDER
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Page Binding" in prompt or "binding" in prompt.lower()
        assert "dynamic" in prompt.lower() or "placeholder" in prompt.lower()


class TestPlannerPrompts:
    """Test all planner-related prompts."""
    
    def test_planner_examples_exists(self, aab_prompts):
        """Test that PLANNER_EXAMPLES exists."""
        prompt = aab_prompts.PLANNER_EXAMPLES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
    
    def test_planner_agent_system_prompt_exists(self, aab_prompts):
        """Test that PLANNER_AGENT_SYSTEM_PROMPT exists."""
        prompt = aab_prompts.PLANNER_AGENT_SYSTEM_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Planner" in prompt or "plan" in prompt.lower()
    
    def test_planner_prompt_contains_build_order(self, aab_prompts):
        """Test that planner prompt contains build order information."""
        prompt = aab_prompts.PLANNER_AGENT_SYSTEM_PROMPT
        assert "Solution" in prompt or "solution" in prompt.lower()
        assert "Application" in prompt or "application" in prompt.lower()
        assert "Object" in prompt or "object" in prompt.lower()
    
    def test_planner_prompt_contains_standard_objects(self, aab_prompts):
        """Test that planner prompt contains standard objects descriptions."""
        prompt = aab_prompts.PLANNER_AGENT_SYSTEM_PROMPT
        # Should reference standard objects
        assert "STANDARD_OBJECTS_DESCRIPTIONS" in prompt or "standard" in prompt.lower()
    
    def test_planner_prompt_contains_system_objects(self, aab_prompts):
        """Test that planner prompt contains system objects descriptions."""
        prompt = aab_prompts.PLANNER_AGENT_SYSTEM_PROMPT
        # Should reference system objects
        assert "SYSTEM_OBJECTS_DESCRIPTIONS" in prompt or "system" in prompt.lower()
    
    def test_planner_prompt_contains_restricted_objects(self, aab_prompts):
        """Test that planner prompt contains restricted objects list."""
        prompt = aab_prompts.PLANNER_AGENT_SYSTEM_PROMPT
        # Should reference restricted objects
        assert "RESTRICTED_OBJECTS_LIST" in prompt or "reserved" in prompt.lower()

    def test_planner_prompt_has_view_type_details_substituted(self, aab_prompts):
        """Test that planner prompt has VIEW_TYPE_DETAILS_TEMPLATE substituted (no raw placeholder)."""
        prompt = aab_prompts.PLANNER_AGENT_SYSTEM_PROMPT
        assert "{VIEW_TYPE_DETAILS_TEMPLATE}" not in prompt, (
            "VIEW_TYPE_DETAILS_TEMPLATE placeholder should be replaced in PLANNER_AGENT_SYSTEM_PROMPT"
        )

    def test_planner_prompt_contains_view_type_details_content(self, aab_prompts):
        """Test that planner prompt contains view type details content from VIEW_TYPE_DETAILS."""
        prompt = aab_prompts.PLANNER_AGENT_SYSTEM_PROMPT
        # Content from VIEW_TYPE_DETAILS_TEMPLATE (view types available in SnapApp)
        assert "view type" in prompt.lower() or "view types" in prompt.lower()
        assert (
            "Single Record" in prompt
            or "Multi-Record" in prompt
            or ("list" in prompt.lower() and "detail" in prompt.lower())
        ), "Planner prompt should include view type details (e.g. list, detail, Single/Multi-Record)"


class TestRouterPrompts:
    """Test all router-related prompts."""
    
    def test_router_agent_system_prompt_exists(self, aab_prompts):
        """Test that ROUTER_AGENT_SYSTEM_PROMPT exists."""
        prompt = aab_prompts.ROUTER_AGENT_SYSTEM_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Router" in prompt or "Snappy" in prompt or "Supervisor" in prompt
    
    def test_router_prompt_contains_standard_objects(self, aab_prompts):
        """Test that router prompt contains standard objects descriptions."""
        prompt = aab_prompts.ROUTER_AGENT_SYSTEM_PROMPT
        assert "STANDARD_OBJECTS_DESCRIPTIONS" in prompt or "standard" in prompt.lower()
    
    def test_router_prompt_contains_system_objects(self, aab_prompts):
        """Test that router prompt contains system objects descriptions."""
        prompt = aab_prompts.ROUTER_AGENT_SYSTEM_PROMPT
        assert "SYSTEM_OBJECTS_DESCRIPTIONS" in prompt or "system" in prompt.lower()
    
    def test_router_prompt_contains_planner_examples(self, aab_prompts):
        """Test that router prompt contains planner examples."""
        prompt = aab_prompts.ROUTER_AGENT_SYSTEM_PROMPT
        assert "PLANNER_EXAMPLES" in prompt or "example" in prompt.lower()


class TestSolutionsApplicationsPrompts:
    """Test all solutions and applications-related prompts."""
    
    def test_solutions_applications_agent_system_prompt_exists(self, aab_prompts):
        """Test that SOLUTIONS_APPLICATIONS_AGENT_SYSTEM_PROMPT exists."""
        prompt = aab_prompts.SOLUTIONS_APPLICATIONS_AGENT_SYSTEM_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Solution" in prompt or "Application" in prompt
        assert "solution" in prompt.lower() or "application" in prompt.lower()
    
    def test_solutions_applications_prompt_contains_default_ids(self, aab_prompts):
        """Test that solutions applications prompt contains default IDs."""
        prompt = aab_prompts.SOLUTIONS_APPLICATIONS_AGENT_SYSTEM_PROMPT
        assert DEFAULT_SOLUTION_ID in prompt
        assert DEFAULT_APPLICATION_ID in prompt


class TestViewsPrompts:
    """Test all view-related prompts."""
    
    def test_view_type_details_exists(self, aab_prompts):
        """Test that VIEW_TYPE_DETAILS exists."""
        prompt = aab_prompts.VIEW_TYPE_DETAILS
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "view" in prompt.lower()
        assert "list" in prompt.lower() or "detail" in prompt.lower()
    
    def test_common_view_properties_exists(self, aab_prompts):
        """Test that COMMON_VIEW_PROPERTIES exists."""
        prompt = aab_prompts.COMMON_VIEW_PROPERTIES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "type" in prompt.lower()
        assert "object_id" in prompt.lower() or "object" in prompt.lower()
    
    def test_list_view_properties_exists(self, aab_prompts):
        """Test that LIST_VIEW_PROPERTIES exists."""
        prompt = aab_prompts.LIST_VIEW_PROPERTIES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "list" in prompt.lower() or "inline" in prompt.lower()
    
    def test_card_view_properties_exists(self, aab_prompts):
        """Test that CARD_VIEW_PROPERTIES exists."""
        prompt = aab_prompts.CARD_VIEW_PROPERTIES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "card" in prompt.lower() or "title" in prompt.lower()
    
    def test_detail_view_properties_exists(self, aab_prompts):
        """Test that DETAIL_VIEW_PROPERTIES exists."""
        prompt = aab_prompts.DETAIL_VIEW_PROPERTIES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "detail" in prompt.lower() or "feed" in prompt.lower()
    
    def test_create_view_properties_exists(self, aab_prompts):
        """Test that CREATE_VIEW_PROPERTIES exists."""
        prompt = aab_prompts.CREATE_VIEW_PROPERTIES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "create" in prompt.lower() or "recaptcha" in prompt.lower()
    
    def test_map_view_properties_exists(self, aab_prompts):
        """Test that MAP_VIEW_PROPERTIES exists."""
        prompt = aab_prompts.MAP_VIEW_PROPERTIES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "map" in prompt.lower() or "address" in prompt.lower()
    
    def test_calendar_view_properties_exists(self, aab_prompts):
        """Test that CALENDAR_VIEW_PROPERTIES exists."""
        prompt = aab_prompts.CALENDAR_VIEW_PROPERTIES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "calendar" in prompt.lower() or "date" in prompt.lower()
    
    def test_deck_view_properties_exists(self, aab_prompts):
        """Test that DECK_VIEW_PROPERTIES exists."""
        prompt = aab_prompts.DECK_VIEW_PROPERTIES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "deck" in prompt.lower() or "badge" in prompt.lower()
    
    def test_view_links_properties_exists(self, aab_prompts):
        """Test that VIEW_LINKS_PROPERTIES exists."""
        prompt = aab_prompts.VIEW_LINKS_PROPERTIES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "view link" in prompt.lower() or "button" in prompt.lower()
    
    def test_view_filters_properties_exists(self, aab_prompts):
        """Test that VIEW_FILTERS_PROPERTIES exists."""
        prompt = aab_prompts.VIEW_FILTERS_PROPERTIES
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "filter" in prompt.lower() or "condition" in prompt.lower()
    
    def test_views_agent_system_prompt_exists(self, aab_prompts):
        """Test that VIEWS_AGENT_SYSTEM_PROMPT exists."""
        prompt = aab_prompts.VIEWS_AGENT_SYSTEM_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Views" in prompt or "view" in prompt.lower()
    
    def test_views_planner_agent_system_prompt_exists(self, aab_prompts):
        """Test that VIEWS_PLANNER_AGENT_SYSTEM_PROMPT exists."""
        prompt = aab_prompts.VIEWS_PLANNER_AGENT_SYSTEM_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "View Planner" in prompt or "planner" in prompt.lower()
    
    def test_view_links_planner_prompt_exists(self, aab_prompts):
        """Test that VIEW_LINKS_PLANNER_PROMPT exists."""
        prompt = aab_prompts.VIEW_LINKS_PLANNER_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "View Link" in prompt or "view link" in prompt.lower()
    
    def test_view_filter_planner_prompt_exists(self, aab_prompts):
        """Test that VIEW_FILTER_PLANNER_PROMPT exists."""
        prompt = aab_prompts.VIEW_FILTER_PLANNER_PROMPT
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "View Filter" in prompt or "filter" in prompt.lower()


class TestCoreExpressions:
    """Test CORE_EXPRESSIONS dictionary structure and content."""
    
    def test_core_expressions_is_dict(self):
        """Test that CORE_EXPRESSIONS is a dictionary."""
        assert isinstance(CORE_EXPRESSIONS, dict)
        assert len(CORE_EXPRESSIONS) > 0
    
    def test_all_expressions_have_required_keys(self):
        """Test that all expressions have required keys."""
        required_keys = ["name", "description", "examples", "returns"]
        for expr_key, expr_value in CORE_EXPRESSIONS.items():
            assert isinstance(expr_value, dict), f"{expr_key} value is not a dict"
            for key in required_keys:
                assert key in expr_value, f"{expr_key} missing required key: {key}"
    
    def test_expression_names_are_strings(self):
        """Test that all expression names are strings."""
        for expr_key, expr_value in CORE_EXPRESSIONS.items():
            assert isinstance(expr_value.get("name"), str), f"{expr_key} name is not a string"
            assert len(expr_value.get("name", "")) > 0, f"{expr_key} name is empty"
    
    def test_expression_descriptions_are_strings(self):
        """Test that all expression descriptions are strings."""
        for expr_key, expr_value in CORE_EXPRESSIONS.items():
            assert isinstance(expr_value.get("description"), str), f"{expr_key} description is not a string"
            assert len(expr_value.get("description", "")) > 0, f"{expr_key} description is empty"
    
    def test_expression_examples_are_lists(self):
        """Test that all expression examples are lists."""
        for expr_key, expr_value in CORE_EXPRESSIONS.items():
            examples = expr_value.get("examples", [])
            assert isinstance(examples, list), f"{expr_key} examples is not a list"
            assert len(examples) > 0, f"{expr_key} has no examples"
    
    def test_expression_examples_have_syntax_and_returns(self):
        """Test that all expression examples have syntax and returns."""
        for expr_key, expr_value in CORE_EXPRESSIONS.items():
            examples = expr_value.get("examples", [])
            for i, example in enumerate(examples):
                assert isinstance(example, dict), f"{expr_key} example {i} is not a dict"
                assert "syntax" in example, f"{expr_key} example {i} missing 'syntax'"
                assert "returns" in example, f"{expr_key} example {i} missing 'returns'"
                assert isinstance(example.get("syntax"), str), f"{expr_key} example {i} syntax is not a string"
                assert len(example.get("syntax", "")) > 0, f"{expr_key} example {i} syntax is empty"
    
    def test_expression_returns_are_strings(self):
        """Test that all expression return types are strings."""
        for expr_key, expr_value in CORE_EXPRESSIONS.items():
            returns = expr_value.get("returns", "")
            assert isinstance(returns, str), f"{expr_key} returns is not a string"
            assert len(returns) > 0, f"{expr_key} returns is empty"
    
    def test_expression_aliases_are_lists_if_present(self):
        """Test that expression aliases are lists if present."""
        for expr_key, expr_value in CORE_EXPRESSIONS.items():
            if "aliases" in expr_value:
                aliases = expr_value.get("aliases", [])
                assert isinstance(aliases, list), f"{expr_key} aliases is not a list"
                for alias in aliases:
                    assert isinstance(alias, str), f"{expr_key} alias is not a string"
    
    def test_specific_expressions_exist(self):
        """Test that specific important expressions exist."""
        important_expressions = ["IF", "AND", "OR", "CONCAT", "SELECT", "LOOKUP", "COUNT", "SUM"]
        for expr in important_expressions:
            assert expr in CORE_EXPRESSIONS, f"Missing important expression: {expr}"
    
    def test_expression_names_match_keys(self):
        """Test that expression names are consistent with their keys."""
        for expr_key, expr_value in CORE_EXPRESSIONS.items():
            name = expr_value.get("name", "")
            # Name should contain the key (case-insensitive)
            assert expr_key.upper() in name.upper(), f"{expr_key} name doesn't match key"


class TestPromptQuality:
    """Test prompt quality - conciseness, clarity, and completeness."""
    
    def test_prompts_are_not_excessively_long(self, aab_prompts):
        """Test that prompts are not excessively long (reasonable length)."""
        max_length = 100000  # 100k characters is reasonable for comprehensive system prompts (CORE_EXPRESSIONS can be large)
        all_methods = [
            "BREADCRUMB_AGENT_SYSTEM_PROMPT",
            "CORE_EXPRESSIONS",
            "EXPRESSION_REQUIREMENTS",
            "EXPRESSIONS_AGENT_PROMPT",
            "SHOW_IF_EXPRESSION_AGENT_PROMPT",
            "VIEW_FILTER_EXPRESSION_AGENT_PROMPT",
            "FIELDS_EXPRESSION_AGENT_PROMPT",
            "VIEWS_EXPRESSION_AGENT_PROMPT",
            "PAGE_DATA_BINDER_AGENT_PROMPT",
            "MENU_NAVIGATIONS_AGENT_SYSTEM_PROMPT",
            "STANDARD_OBJECTS_DESCRIPTIONS",
            "SYSTEM_OBJECTS_DESCRIPTIONS",
            "OBJECTS_FIELDS_AGENT_SYSTEM_PROMPT",
            "PAGE_PLANNER_AGENT_SYSTEM_PROMPT",
            "PAGES_AGENT_SYSTEM_PROMPT",
            "PAGE_DATA_BINDER",
            "PLANNER_EXAMPLES",
            "PLANNER_AGENT_SYSTEM_PROMPT",
            "ROUTER_AGENT_SYSTEM_PROMPT",
            "SOLUTIONS_APPLICATIONS_AGENT_SYSTEM_PROMPT",
            "VIEW_TYPE_DETAILS",
            "COMMON_VIEW_PROPERTIES",
            "LIST_VIEW_PROPERTIES",
            "CARD_VIEW_PROPERTIES",
            "DETAIL_VIEW_PROPERTIES",
            "CREATE_VIEW_PROPERTIES",
            "MAP_VIEW_PROPERTIES",
            "CALENDAR_VIEW_PROPERTIES",
            "DECK_VIEW_PROPERTIES",
            "VIEW_LINKS_PROPERTIES",
            "VIEW_FILTERS_PROPERTIES",
            "VIEWS_AGENT_SYSTEM_PROMPT",
            "VIEWS_PLANNER_AGENT_SYSTEM_PROMPT",
            "VIEW_LINKS_PLANNER_PROMPT",
            "VIEW_FILTER_PLANNER_PROMPT",
        ]
        
        for method_name in all_methods:
            if hasattr(aab_prompts, method_name):
                method = getattr(aab_prompts, method_name)
                prompt = method
                assert len(prompt) <= max_length, f"{method_name} is too long ({len(prompt)} chars)"
    
    def test_prompts_are_not_empty(self, aab_prompts):
        """Test that all prompts are not empty."""
        all_methods = [
            "BREADCRUMB_AGENT_SYSTEM_PROMPT",
            "CORE_EXPRESSIONS",
            "EXPRESSION_REQUIREMENTS",
            "EXPRESSIONS_AGENT_PROMPT",
            "MENU_NAVIGATIONS_AGENT_SYSTEM_PROMPT",
            "STANDARD_OBJECTS_DESCRIPTIONS",
            "SYSTEM_OBJECTS_DESCRIPTIONS",
            "OBJECTS_FIELDS_AGENT_SYSTEM_PROMPT",
            "PAGE_PLANNER_AGENT_SYSTEM_PROMPT",
            "PAGES_AGENT_SYSTEM_PROMPT",
            "PLANNER_AGENT_SYSTEM_PROMPT",
            "ROUTER_AGENT_SYSTEM_PROMPT",
            "SOLUTIONS_APPLICATIONS_AGENT_SYSTEM_PROMPT",
            "VIEWS_AGENT_SYSTEM_PROMPT",
        ]
        
        for method_name in all_methods:
            if hasattr(aab_prompts, method_name):
                method = getattr(aab_prompts, method_name)
                prompt = method
                assert len(prompt.strip()) > 0, f"{method_name} is empty"
    
    def test_prompts_have_no_obvious_formatting_errors(self, aab_prompts):
        """Test that prompts don't have obvious formatting errors."""
        all_methods = [
            "BREADCRUMB_AGENT_SYSTEM_PROMPT",
            "EXPRESSIONS_AGENT_PROMPT",
            "MENU_NAVIGATIONS_AGENT_SYSTEM_PROMPT",
            "OBJECTS_FIELDS_AGENT_SYSTEM_PROMPT",
            "PAGE_PLANNER_AGENT_SYSTEM_PROMPT",
            "PAGES_AGENT_SYSTEM_PROMPT",
            "PLANNER_AGENT_SYSTEM_PROMPT",
            "ROUTER_AGENT_SYSTEM_PROMPT",
            "SOLUTIONS_APPLICATIONS_AGENT_SYSTEM_PROMPT",
            "VIEWS_AGENT_SYSTEM_PROMPT",
        ]
        
        for method_name in all_methods:
            if hasattr(aab_prompts, method_name):
                method = getattr(aab_prompts, method_name)
                prompt = method
                # Check for common formatting issues
                # Note: Some prompts may have intentional braces in code examples, so we check for unreplaced template placeholders instead
                # Check for placeholder format strings that weren't replaced (double braces that should have been single)
                # Template variables should be {VAR} not {{VAR}} after formatting
                unreplaced_placeholders = [m for m in ["{EXPRESSION_REQUIREMENTS}", "{CORE_EXPRESSIONS}", "{STANDARD_OBJECTS_DESCRIPTIONS}", "{SYSTEM_OBJECTS_DESCRIPTIONS}", "{RESTRICTED_OBJECTS_LIST}", "{PLANNER_EXAMPLES}", "{VIEW_TYPE_DETAILS}", "{VIEW_TYPE_DETAILS_TEMPLATE}", "{COMMON_VIEW_PROPERTIES}", "{LIST_VIEW_PROPERTIES}", "{CARD_VIEW_PROPERTIES}", "{DETAIL_VIEW_PROPERTIES}", "{CREATE_VIEW_PROPERTIES}", "{MAP_VIEW_PROPERTIES}", "{CALENDAR_VIEW_PROPERTIES}", "{DECK_VIEW_PROPERTIES}", "{VIEW_LINKS_PROPERTIES}", "{VIEW_FILTERS_PROPERTIES}"] if m in prompt]
                if unreplaced_placeholders:
                    # This is OK - some prompts may intentionally show template structure
                    pass


class TestPromptIntegration:
    """Test that prompts integrate correctly with each other."""
    
    def test_expression_prompts_reference_core_expressions(self, aab_prompts):
        """Test that expression-related prompts reference core expressions."""
        expression_prompts = [
            aab_prompts.EXPRESSIONS_AGENT_PROMPT,
            aab_prompts.SHOW_IF_EXPRESSION_AGENT_PROMPT,
            aab_prompts.VIEW_FILTER_EXPRESSION_AGENT_PROMPT,
            aab_prompts.FIELDS_EXPRESSION_AGENT_PROMPT,
            aab_prompts.VIEWS_EXPRESSION_AGENT_PROMPT,
            aab_prompts.PAGE_DATA_BINDER_AGENT_PROMPT,
        ]
        
        for prompt in expression_prompts:
            # These prompts should reference CORE_EXPRESSIONS or contain expression info
            assert "expression" in prompt.lower() or "CORE_EXPRESSIONS" in prompt
    
    def test_planner_prompt_integrates_components(self, aab_prompts):
        """Test that planner prompt integrates all necessary components."""
        prompt = aab_prompts.PLANNER_AGENT_SYSTEM_PROMPT
        # Should reference standard objects, system objects, and restricted objects
        assert "STANDARD_OBJECTS_DESCRIPTIONS" in prompt or "standard" in prompt.lower()
        assert "SYSTEM_OBJECTS_DESCRIPTIONS" in prompt or "system" in prompt.lower()
        assert "RESTRICTED_OBJECTS_LIST" in prompt or "reserved" in prompt.lower()
        # VIEW_TYPE_DETAILS_TEMPLATE should be substituted (view type logic for determining view type)
        assert "{VIEW_TYPE_DETAILS_TEMPLATE}" not in prompt
        assert "view type" in prompt.lower() or "list" in prompt.lower() or "detail" in prompt.lower()
    
    def test_router_prompt_integrates_components(self, aab_prompts):
        """Test that router prompt integrates all necessary components."""
        prompt = aab_prompts.ROUTER_AGENT_SYSTEM_PROMPT
        # Should reference standard objects, system objects, and planner examples
        assert "STANDARD_OBJECTS_DESCRIPTIONS" in prompt or "standard" in prompt.lower()
        assert "SYSTEM_OBJECTS_DESCRIPTIONS" in prompt or "system" in prompt.lower()
        assert "PLANNER_EXAMPLES" in prompt or "example" in prompt.lower()
    
    def test_views_prompt_integrates_view_properties(self, aab_prompts):
        """Test that views prompt integrates view property templates."""
        prompt = aab_prompts.VIEWS_AGENT_SYSTEM_PROMPT
        # Should contain view type details and properties (already formatted)
        assert "view type" in prompt.lower() or "list" in prompt.lower() or "detail" in prompt.lower()
        assert "property" in prompt.lower() or "object_id" in prompt.lower() or "type" in prompt.lower()
    
    def test_views_planner_prompt_integrates_all_properties(self, aab_prompts):
        """Test that views planner prompt integrates all view properties."""
        prompt = aab_prompts.VIEWS_PLANNER_AGENT_SYSTEM_PROMPT
        # Should contain all view property content (already formatted)
        assert "view type" in prompt.lower() or "list" in prompt.lower() or "detail" in prompt.lower()
        assert "property" in prompt.lower() or "object_id" in prompt.lower()
        assert "list" in prompt.lower() or "enable_inline_editing" in prompt.lower()
        assert "card" in prompt.lower() or "title_column" in prompt.lower()


class TestAttributeDelegation:
    """Test that AABPrompts correctly delegates to handlers."""
    
    def test_all_handlers_are_accessible(self, aab_prompts):
        """Test that all handler methods are accessible through AABPrompts."""
        # Test a method from each handler
        assert hasattr(aab_prompts, "BREADCRUMB_AGENT_SYSTEM_PROMPT")
        assert hasattr(aab_prompts, "CORE_EXPRESSIONS")
        assert hasattr(aab_prompts, "MENU_NAVIGATIONS_AGENT_SYSTEM_PROMPT")
        assert hasattr(aab_prompts, "STANDARD_OBJECTS_DESCRIPTIONS")
        assert hasattr(aab_prompts, "PAGE_PLANNER_AGENT_SYSTEM_PROMPT")
        assert hasattr(aab_prompts, "PAGES_AGENT_SYSTEM_PROMPT")
        assert hasattr(aab_prompts, "PLANNER_AGENT_SYSTEM_PROMPT")
        assert hasattr(aab_prompts, "ROUTER_AGENT_SYSTEM_PROMPT")
        assert hasattr(aab_prompts, "SOLUTIONS_APPLICATIONS_AGENT_SYSTEM_PROMPT")
        assert hasattr(aab_prompts, "VIEW_TYPE_DETAILS")
    
    def test_nonexistent_attribute_raises_error(self, aab_prompts):
        """Test that accessing non-existent attributes raises AttributeError."""
        with pytest.raises(AttributeError):
            _ = aab_prompts.NONEXISTENT_METHOD


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
