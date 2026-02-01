from prompts.breadcrumbs import BREADCRUMB_AGENT_SYSTEM_PROMPT_TEMPLATE
from prompts.expressions import (
    EXPRESSION_REQUIREMENTS_TEMPLATE,
    EXPRESSIONS_AGENT_PROMPT_TEMPLATE,
    FIELDS_EXPRESSION_AGENT_PROMPT_TEMPLATE,
    INITIAL_VALUE_EXAMPLES_TEMPLATE,
    PAGE_DATA_BINDER_AGENT_PROMPT_TEMPLATE,
    SHOW_IF_EXPRESSION_AGENT_PROMPT_TEMPLATE,
    VIEW_FILTER_EXPRESSION_AGENT_PROMPT_TEMPLATE,
    VIEWS_EXPRESSION_AGENT_PROMPT_TEMPLATE,
)
from prompts.menu_navigations import MENU_NAVIGATIONS_AGENT_SYSTEM_PROMPT_TEMPLATE
from prompts.objects_fields import OBJECTS_FIELDS_AGENT_SYSTEM_PROMPT_TEMPLATE, STANDARD_OBJECTS_DESCRIPTIONS_TEMPLATE, SYSTEM_OBJECTS_DESCRIPTIONS_TEMPLATE
from prompts.page_planner import PAGE_PLANNER_AGENT_SYSTEM_PROMPT_TEMPLATE
from prompts.pages import PAGE_DATA_BINDER_TEMPLATE, PAGES_AGENT_SYSTEM_PROMPT_TEMPLATE
from prompts.planner import PLANNER_AGENT_SYSTEM_PROMPT_TEMPLATE, PLANNER_EXAMPLES_TEMPLATE
from prompts.router import ROUTER_AGENT_SYSTEM_PROMPT_TEMPLATE
from prompts.solutions_applications import SOLUTIONS_APPLICATIONS_AGENT_SYSTEM_PROMPT_TEMPLATE
from prompts.view_filter_planner import VIEW_FILTER_PLANNER_PROMPT_TEMPLATE
from prompts.view_links_planner import VIEW_LINKS_PLANNER_PROMPT_TEMPLATE
from prompts.view_planner import VIEWS_PLANNER_AGENT_SYSTEM_PROMPT_TEMPLATE
from prompts.views import CALENDAR_VIEW_PROPERTIES_TEMPLATE, CARD_VIEW_PROPERTIES_TEMPLATE, COMMON_VIEW_PROPERTIES_TEMPLATE, CREATE_VIEW_PROPERTIES_TEMPLATE, DECK_VIEW_PROPERTIES_TEMPLATE, DETAIL_VIEW_PROPERTIES_TEMPLATE, LIST_VIEW_PROPERTIES_TEMPLATE, MAP_VIEW_PROPERTIES_TEMPLATE, VIEW_FILTERS_PROPERTIES_TEMPLATE, VIEW_LINKS_PROPERTIES_TEMPLATE, VIEW_TYPE_DETAILS_TEMPLATE, VIEWS_AGENT_SYSTEM_PROMPT_TEMPLATE


class _BreadcrumbsHandler:
    """Handler for all breadcrumb-related prompts."""
    
    @property
    def BREADCRUMB_AGENT_SYSTEM_PROMPT(self) -> str:
        return BREADCRUMB_AGENT_SYSTEM_PROMPT_TEMPLATE


class _ExpressionsHandler:
    """Handler for all expression-related prompts."""
    
    def __init__(self, core_expressions: dict) -> None:
        self.core_expressions = core_expressions
    
    def _generate_system_prompt(self, expressions: dict) -> str:
        sections: list[str] = []

        for key, value in expressions.items():
            name = value.get("name", "")
            description = value.get("description", "")
            examples = value.get("examples", [])
            return_type = value.get("returns", "")
            aliases = value.get("aliases", [])

            example_lines = (
                "\n".join(
                    f"- {ex.get('syntax')} → {ex.get('returns')}" for ex in examples
                )
                or "None"
            )

            alias_lines = (
                "\n".join(f"- {alias}" for alias in aliases) if aliases else "None"
            )

            sections.append(
                f"""- ### {key}

                    Function Signature:
                    {name}

                    Description:
                    {description}

                    Return Type:
                    {return_type}

                    Aliases:
                    {alias_lines}

                    Examples:
                    {example_lines}
                    """
            )

        return "\n".join(sections)

    @property
    def CORE_EXPRESSIONS(self) -> str:
        return f"""
                ## Built in Core Expressions

                The following are the core expressions available in SnapApp:

                {self._generate_system_prompt(self.core_expressions)}
                """
    
    @property
    def EXPRESSION_REQUIREMENTS(self) -> str:
        return EXPRESSION_REQUIREMENTS_TEMPLATE
    
    @property
    def EXPRESSIONS_AGENT_PROMPT(self) -> str:
        return EXPRESSIONS_AGENT_PROMPT_TEMPLATE.format(
            EXPRESSION_REQUIREMENTS=self.EXPRESSION_REQUIREMENTS,
            CORE_EXPRESSIONS=self.CORE_EXPRESSIONS,
        )
    
    @property
    def SHOW_IF_EXPRESSION_AGENT_PROMPT(self) -> str:
        return SHOW_IF_EXPRESSION_AGENT_PROMPT_TEMPLATE.format(
            EXPRESSION_REQUIREMENTS=self.EXPRESSION_REQUIREMENTS,
            CORE_EXPRESSIONS=self.CORE_EXPRESSIONS,
        )
    
    @property
    def INITIAL_VALUE_EXAMPLES(self) -> str:
        return INITIAL_VALUE_EXAMPLES_TEMPLATE
    
    @property
    def VIEW_FILTER_EXPRESSION_AGENT_PROMPT(self) -> str:
        return VIEW_FILTER_EXPRESSION_AGENT_PROMPT_TEMPLATE.format(
            EXPRESSION_REQUIREMENTS=self.EXPRESSION_REQUIREMENTS,
            CORE_EXPRESSIONS=self.CORE_EXPRESSIONS,
        )

    @property
    def FIELDS_EXPRESSION_AGENT_PROMPT(self) -> str:
        return FIELDS_EXPRESSION_AGENT_PROMPT_TEMPLATE.format(
            EXPRESSION_REQUIREMENTS=self.EXPRESSION_REQUIREMENTS,
            CORE_EXPRESSIONS=self.CORE_EXPRESSIONS,
        )
    
    @property
    def VIEWS_EXPRESSION_AGENT_PROMPT(self) -> str:
        return VIEWS_EXPRESSION_AGENT_PROMPT_TEMPLATE.format(
            EXPRESSION_REQUIREMENTS=self.EXPRESSION_REQUIREMENTS,
            CORE_EXPRESSIONS=self.CORE_EXPRESSIONS,
        )
    
    @property
    def PAGE_DATA_BINDER_AGENT_PROMPT(self) -> str:
        return PAGE_DATA_BINDER_AGENT_PROMPT_TEMPLATE.format(
            EXPRESSION_REQUIREMENTS=self.EXPRESSION_REQUIREMENTS,
            CORE_EXPRESSIONS=self.CORE_EXPRESSIONS,
        )

class _MenuNavigationsHandler:
    """Handler for all menu navigation-related prompts."""
    
    @property
    def MENU_NAVIGATIONS_AGENT_SYSTEM_PROMPT(self) -> str:
        return MENU_NAVIGATIONS_AGENT_SYSTEM_PROMPT_TEMPLATE


class _ObjectsFieldsHandler:
    """Handler for all object and field-related prompts."""
    
    def __init__(self, restricted_objects_list: list[str]) -> None:
        self.restricted_objects_list = restricted_objects_list
    
    @property
    def STANDARD_OBJECTS_DESCRIPTIONS(self) -> str:
        return STANDARD_OBJECTS_DESCRIPTIONS_TEMPLATE
    
    @property
    def SYSTEM_OBJECTS_DESCRIPTIONS(self) -> str:
        return SYSTEM_OBJECTS_DESCRIPTIONS_TEMPLATE

    @property
    def OBJECTS_FIELDS_AGENT_SYSTEM_PROMPT(self) -> str:
        return OBJECTS_FIELDS_AGENT_SYSTEM_PROMPT_TEMPLATE.format(
            RESTRICTED_OBJECTS_LIST=", ".join(self.restricted_objects_list),
        )


class _PagePlannerHandler:
    """Handler for all page planner-related prompts."""
    
    @property
    def PAGE_PLANNER_AGENT_SYSTEM_PROMPT(self) -> str:
        return PAGE_PLANNER_AGENT_SYSTEM_PROMPT_TEMPLATE


class _PagesHandler:
    """Handler for all page-related prompts."""
    
    @property
    def PAGES_AGENT_SYSTEM_PROMPT(self) -> str:
        return PAGES_AGENT_SYSTEM_PROMPT_TEMPLATE
    
    @property
    def PAGE_DATA_BINDER(self) -> str:
        return PAGE_DATA_BINDER_TEMPLATE


class _PlannerHandler:
    """Handler for all planner-related prompts."""
    
    def __init__(self, restricted_objects_list: list[str], standard_objects_descriptions: str, system_objects_descriptions: str, view_type_details_template: str) -> None:
        self.restricted_objects_list = restricted_objects_list
        self.standard_objects_descriptions = standard_objects_descriptions
        self.system_objects_descriptions = system_objects_descriptions
        self.view_type_details_template = view_type_details_template
    
    @property
    def PLANNER_EXAMPLES(self) -> str:
        return '\n\n\n'.join(PLANNER_EXAMPLES_TEMPLATE)
    
    @property
    def PLANNER_AGENT_SYSTEM_PROMPT(self) -> str:
        return PLANNER_AGENT_SYSTEM_PROMPT_TEMPLATE.format(
            RESTRICTED_OBJECTS_LIST=", ".join(self.restricted_objects_list),
            STANDARD_OBJECTS_DESCRIPTIONS=self.standard_objects_descriptions,
            SYSTEM_OBJECTS_DESCRIPTIONS=self.system_objects_descriptions,
            PLANNER_EXAMPLES=self.PLANNER_EXAMPLES,
            VIEW_TYPE_DETAILS_TEMPLATE=self.view_type_details_template,
        )


class _RouterHandler:
    """Handler for all router-related prompts."""
    
    def __init__(self, standard_objects_descriptions: str, system_objects_descriptions: str, planner_examples: list[str]) -> None:
        self.standard_objects_descriptions = standard_objects_descriptions
        self.system_objects_descriptions = system_objects_descriptions
        self.planner_examples = planner_examples
    
    @property
    def ROUTER_AGENT_SYSTEM_PROMPT(self) -> str:
        return ROUTER_AGENT_SYSTEM_PROMPT_TEMPLATE.format(
            STANDARD_OBJECTS_DESCRIPTIONS=self.standard_objects_descriptions,
            SYSTEM_OBJECTS_DESCRIPTIONS=self.system_objects_descriptions,
            PLANNER_EXAMPLES=self.planner_examples,
        )


class _SolutionsApplicationsHandler:
    """Handler for all solutions and applications-related prompts."""
    
    def __init__(self, default_solution_id: str, default_application_id: str) -> None:
        self.default_solution_id = default_solution_id
        self.default_application_id = default_application_id
    
    @property
    def SOLUTIONS_APPLICATIONS_AGENT_SYSTEM_PROMPT(self) -> str:
        return SOLUTIONS_APPLICATIONS_AGENT_SYSTEM_PROMPT_TEMPLATE.format(
            DEFAULT_SOLUTION_ID=self.default_solution_id,
            DEFAULT_APPLICATION_ID=self.default_application_id,
        )


class _ViewsHandler:
    """Handler for all view-related prompts."""

    @property
    def VIEW_TYPE_DETAILS(self) -> str:
        return VIEW_TYPE_DETAILS_TEMPLATE
    
    @property
    def COMMON_VIEW_PROPERTIES(self) -> str:
        return COMMON_VIEW_PROPERTIES_TEMPLATE
    
    @property
    def LIST_VIEW_PROPERTIES(self) -> str:
        return LIST_VIEW_PROPERTIES_TEMPLATE
    
    @property
    def CARD_VIEW_PROPERTIES(self) -> str:
        return CARD_VIEW_PROPERTIES_TEMPLATE

    @property
    def DETAIL_VIEW_PROPERTIES(self) -> str:
        return DETAIL_VIEW_PROPERTIES_TEMPLATE

    @property
    def CREATE_VIEW_PROPERTIES(self) -> str:
        return CREATE_VIEW_PROPERTIES_TEMPLATE

    @property
    def MAP_VIEW_PROPERTIES(self) -> str:
        return MAP_VIEW_PROPERTIES_TEMPLATE
    
    @property
    def CALENDAR_VIEW_PROPERTIES(self) -> str:
        return CALENDAR_VIEW_PROPERTIES_TEMPLATE
    
    @property
    def DECK_VIEW_PROPERTIES(self) -> str:
        return DECK_VIEW_PROPERTIES_TEMPLATE

    @property
    def VIEW_LINKS_PROPERTIES(self) -> str:
        return VIEW_LINKS_PROPERTIES_TEMPLATE

    @property
    def VIEW_FILTERS_PROPERTIES(self) -> str:
        return VIEW_FILTERS_PROPERTIES_TEMPLATE

    @property
    def VIEWS_AGENT_SYSTEM_PROMPT(self) -> str:
        return VIEWS_AGENT_SYSTEM_PROMPT_TEMPLATE.format(
            VIEW_TYPE_DETAILS=self.VIEW_TYPE_DETAILS,
            COMMON_VIEW_PROPERTIES=self.COMMON_VIEW_PROPERTIES,
            LIST_VIEW_PROPERTIES=self.LIST_VIEW_PROPERTIES,
            CARD_VIEW_PROPERTIES=self.CARD_VIEW_PROPERTIES,
            DETAIL_VIEW_PROPERTIES=self.DETAIL_VIEW_PROPERTIES,
            CREATE_VIEW_PROPERTIES=self.CREATE_VIEW_PROPERTIES,
            MAP_VIEW_PROPERTIES=self.MAP_VIEW_PROPERTIES,
            CALENDAR_VIEW_PROPERTIES=self.CALENDAR_VIEW_PROPERTIES,
            DECK_VIEW_PROPERTIES=self.DECK_VIEW_PROPERTIES,
        )

    @property
    def VIEWS_PLANNER_AGENT_SYSTEM_PROMPT(self) -> str:
        return VIEWS_PLANNER_AGENT_SYSTEM_PROMPT_TEMPLATE.format(
            VIEW_TYPE_DETAILS=self.VIEW_TYPE_DETAILS,
            COMMON_VIEW_PROPERTIES=self.COMMON_VIEW_PROPERTIES,
            LIST_VIEW_PROPERTIES=self.LIST_VIEW_PROPERTIES,
            CARD_VIEW_PROPERTIES=self.CARD_VIEW_PROPERTIES,
            DETAIL_VIEW_PROPERTIES=self.DETAIL_VIEW_PROPERTIES,
            CREATE_VIEW_PROPERTIES=self.CREATE_VIEW_PROPERTIES,
            MAP_VIEW_PROPERTIES=self.MAP_VIEW_PROPERTIES,
            CALENDAR_VIEW_PROPERTIES=self.CALENDAR_VIEW_PROPERTIES,
            DECK_VIEW_PROPERTIES=self.DECK_VIEW_PROPERTIES,
            VIEW_LINKS_PROPERTIES=self.VIEW_LINKS_PROPERTIES,
            VIEW_FILTERS_PROPERTIES=self.VIEW_FILTERS_PROPERTIES,
        )

    @property
    def VIEW_LINKS_PLANNER_PROMPT(self) -> str:
        return VIEW_LINKS_PLANNER_PROMPT_TEMPLATE.format(
            VIEW_LINKS_PROPERTIES=self.VIEW_LINKS_PROPERTIES,
        )
    

    @property
    def VIEW_FILTER_PLANNER_PROMPT(self) -> str:
        return VIEW_FILTER_PLANNER_PROMPT_TEMPLATE.format(
            VIEW_FILTERS_PROPERTIES=self.VIEW_FILTERS_PROPERTIES,
        )



class AABPrompts:
    """Main prompts class that coordinates all prompt handlers."""
    
    def __init__(self, core_expressions: dict, restricted_objects_list: list[str], default_solution_id: str, default_application_id: str) -> None:
        # Initialize handlers
        self._objects_fields = _ObjectsFieldsHandler(restricted_objects_list)
        self._views = _ViewsHandler()
        self._planner = _PlannerHandler(
            restricted_objects_list,
            self._objects_fields.STANDARD_OBJECTS_DESCRIPTIONS,
            self._objects_fields.SYSTEM_OBJECTS_DESCRIPTIONS,
            self._views.VIEW_TYPE_DETAILS
        )
        
        # Store all handlers in a list for easy iteration
        self._handlers = [
            _BreadcrumbsHandler(),
            _ExpressionsHandler(core_expressions),
            _MenuNavigationsHandler(),
            self._objects_fields,
            _PagePlannerHandler(),
            _PagesHandler(),
            self._planner,
            _RouterHandler(
                self._objects_fields.STANDARD_OBJECTS_DESCRIPTIONS,
                self._objects_fields.SYSTEM_OBJECTS_DESCRIPTIONS,
                self._planner.PLANNER_EXAMPLES,
            ),
            _SolutionsApplicationsHandler(default_solution_id, default_application_id),
            self._views,
        ]
    
    def __getattr__(self, name: str):
        """Automatically delegate method calls to the appropriate handler."""
        for handler in self._handlers:
            if hasattr(handler, name):
                return getattr(handler, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")



    