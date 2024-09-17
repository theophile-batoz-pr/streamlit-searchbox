"""
module for streamlit searchbox component
"""

from __future__ import annotations

import functools
import logging
import os
import time
import asyncio
from typing import Any, Callable, List, Literal, Tuple, TypedDict, Union

import streamlit as st
import streamlit.components.v1 as components

try:
    from streamlit import rerun as rerun  # type: ignore
except ImportError:
    # conditional import for streamlit version <1.27
    from streamlit import experimental_rerun as rerun  # type: ignore


# point to build directory
parent_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(parent_dir, "frontend/build")
_get_react_component = components.declare_component(
    "searchbox",
    path=build_dir,
)

logger = logging.getLogger(__name__)


def wrap_inactive_session(func):
    """
    session state isn't available anymore due to rerun (as state key can't be empty)
    if the proxy is missing, this thread isn't really active and an early return is noop
    """

    @functools.wraps(func)
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError as error:
            if kwargs.get("key", None) == error.args[0]:
                logger.debug(f"Session Proxy unavailable for key: {error.args[0]}")
                return

            raise error

    return inner_function


def _list_to_options_py(options: list[Any] | list[tuple[str, Any]]) -> list[Any]:
    """
    unpack search options for proper python return types
    """
    return [v[1] if isinstance(v, tuple) else v for v in options]


def _list_to_options_js(
    options: list[Any] | list[tuple[str, Any]]
) -> list[dict[str, Any]]:
    """
    unpack search options for use in react component
    """
    if len(options) > 0 and isinstance(options[0], dict) and options[0].get("label"):
        return options
    return [
        {
            "label": str(v[0]) if isinstance(v, tuple) else str(v),
            "value": str(v[0]) if isinstance(v, tuple) else str(v),
        }
        for i, v in enumerate(options)
    ]


def _process_search(
    search_function: Callable[[str], List[Any]],
    key: str,
    searchterm: str,
    **kwargs,
) -> bool:
    # nothing changed, avoid new search
    if searchterm == st.session_state[key]["search"]:
        return False

    st.session_state[key]["search"] = searchterm
    search_results = search_function(searchterm, **kwargs)
    if search_results is None:
        search_results = []

    st.session_state[key]["options_js"] = _list_to_options_js(search_results)
    st.session_state[key]["options_py"] = _list_to_options_py(search_results)
    
    return True

def _set_defaults(
    key: str,
    is_multi: bool,
    default: Any,
    default_options: List[Any] | None = None,
) -> None:
    default_key_react = f"{key}_react_{str(time.time())}"
    key_react = st.session_state.get(key, {}).get("key_react", default_key_react)
    st.session_state[key] = {
        # updated after each selection / reset
        "result": default if default is not None else None,
        # updated after each search keystroke
        "search": default if default is not None and not is_multi else "",
        # updated after each search_function run
        "options_js": [{"value": default, "label": default}] if (default is not None and not is_multi) else default_options,
        # key that is used by react component, use time suffix to reload after clear
        "key_react": key_react,
    }

    if not default and default_options:
        st.session_state[key]["options_js"] = _list_to_options_js(default_options)
        st.session_state[key]["options_py"] = _list_to_options_py(default_options)

ClearStyle = TypedDict(
    "ClearStyle",
    {
        # determines which icon is used for the clear button
        "icon": Literal["circle-unfilled", "circle-filled", "cross"],
        # further css styles for the clear button
        "width": int,
        "height": int,
        "fill": str,
        "stroke": str,
        "stroke-width": int,
    },
    total=False,
)

DropdownStyle = TypedDict(
    "DropdownStyle",
    {
        # weither to flip the dropdown if the menu is open
        "rotate": bool,
        # further css styles for the dropdown
        "width": int,
        "height": int,
        "fill": str,
    },
    total=False,
)


class SearchboxStyle(TypedDict, total=False):
    globalContainer: dict | None
    label: dict | None
    menuList: dict | None
    singleValue: dict | None
    input: dict | None
    placeholder: dict | None
    control: dict | None
    option: dict | None


class StyleOverrides(TypedDict, total=False):
    clear: ClearStyle | None
    dropdown: DropdownStyle | None
    searchbox: SearchboxStyle | None


@wrap_inactive_session
def st_searchbox(
    search_function: Callable[[str], List[Any]],
    placeholder: str = "Search ...",
    label: str | None = None,
    title: str | None = None,
    button: str | None = None,
    css_prefix: str | None = None,
    global_css: str | None = None,
    on_button_click: Callable[[str], None] | None = None,
    default: Any = None,
    default_options: List[Any] | None = None,
    clear_on_submit: bool = False,
    rerun_on_update: bool = True,
    debounce: int = 100,
    edit_after_submit: Literal["disabled", "current", "option", "concat"] = "disabled",
    style_overrides: StyleOverrides | None = None,
    key: str = "searchbox",
    **kwargs,
) -> Any:
    """
    Create a new searchbox instance, that provides suggestions based on the user input
    and returns a selected option or empty string if nothing was selected

    Args:
        search_function (Callable[[str], List[any]]):
            Function that is called to fetch new suggestions after user input.
        placeholder (str, optional):
            Label shown in the searchbox. Defaults to "Search ...".
        label (str, optional):
            Label shown above the searchbox. Defaults to None.
        default (any, optional):
            Return value if nothing is selected so far. Defaults to None.
        default_options (List[any], optional):
            Initial list of options. Defaults to None.
        clear_on_submit (bool, optional):
            Remove suggestions on select. Defaults to False.
        rerun_on_update (bool, optional):
            Rerun the streamlit app after each search. Defaults to True.
        edit_after_submit ("disabled", "current", "option", "concat", optional):
            Edit the search term after submit. Defaults to "disabled".
        style_overrides (StyleOverrides, optional):
            CSS styling passed directly to the react components. Defaults to None.
        key (str, optional):
            Streamlit session key. Defaults to "searchbox".

    Returns:
        any: based on user selection
    """

    if key not in st.session_state:
        _set_defaults(key, False, default, default_options)

    # everything here is passed to react as this.props.args
    react_state = _get_react_component(
        key=st.session_state[key]["key_react"],
        propsList=[{
            "options": st.session_state[key]["options_js"],
            "clear_on_submit": clear_on_submit,
            "placeholder": placeholder,
            "label": label,
            "edit_after_submit": edit_after_submit,
            "style_overrides": style_overrides,
            "debounce": debounce,
            "title": title,
            "button": button,
            "css_prefix": css_prefix,
            "global_css": global_css,
            # react return state within streamlit session_state
            "key": st.session_state[key]["key_react"],
            "option_source": st.session_state[key]["search"]
        }]
    )
    if react_state is None:
        return st.session_state[key]["result"]
    else:
        react_state = react_state[0]
    interaction, value = react_state["interaction"], react_state["value"]

    if interaction == "search":
        # triggers rerun, no ops afterwards executed
        should_rerun = _process_search(search_function, key, value, **kwargs)
        if rerun_on_update and should_rerun:
            rerun()


    if interaction == "button-click" and on_button_click is not None:
        val = st.session_state[key]["search"]
        on_button_click(val)

    if interaction == "submit":
        st.session_state[key]["search"] = value
        st.session_state[key]["result"] = (
            st.session_state[key]["options_py"][value]
            if "options_py" in st.session_state[key]
            else value
        )
        return st.session_state[key]["result"]

    if interaction == "reset":
        _set_defaults(key, False, None, default_options)

        if rerun_on_update:
            rerun()

        return default

    # no new react interaction happened
    return st.session_state[key]["result"]

DatetimepickerProps = TypedDict(
    "DatetimepickerProps",
    {
        "datetimepicker_props": dict[str, str],
        "key": str,
        "label": str,
        "min": str,
        "max": str,
        "global_css": str
    },
    total=False,
)
SearchboxProps = TypedDict(
    "SearchboxProps",
    {
        "search_function": Callable[[str], List[Any]],
        "placeholder": str,
        "label": str | None,
        "title": str | None,
        "title_picto": str | None,
        "button": str | None,
        "button_picto": str | None,
        "css_prefix": str | None,
        "global_css": str | None,
        "on_button_click": Callable[[str, Any], None] | None,
        "default": Any,
        "persistant_default": bool,
        "default_options": List[Any] | None,
        "clear_on_submit": bool,
        "rerun_on_update": bool,
        "debounce": int,
        "edit_after_submit": Literal["disabled", "current", "option", "concat"],
        "style_overrides": StyleOverrides | None,
        "key": str,
        "is_multi": bool,
    },
    total=False,
)

def set_defaults_simplified(
    key: str,
    is_multi: bool,
    default: Any,
    default_options: List[Any] | None = None,
) -> None:
    default_key_react = f"{key}_react_{str(time.time())}"
    key_react = st.session_state.get(key, {}).get("key_react", default_key_react)
    default_options_js = []
    if default is not None and not is_multi:
        default_options_js = [{"value": default, "label": default}]
    elif default_options is not None:
        default_options_js = _list_to_options_js(default_options)
    st.session_state[key] = {
        # updated after each selection / reset
        "result": default if default is not None else None,
        # updated after each search keystroke
        "search": default if default is not None and not is_multi else "",
        # updated after each search_function run
        "options_js": default_options_js,
        # key that is used by react component, use time suffix to reload after clear
        "key_react": key_react,
    }

    if not default and default_options:
        st.session_state[key]["options_js"] = _list_to_options_js(default_options)

def process_search_simplified(
    search_function: Callable[[str], List[Any]],
    key: str,
    searchterm: str,
    **kwargs,
) -> bool:
    # nothing changed, avoid new search
    if searchterm == st.session_state[key]["search"]:
        return False

    st.session_state[key]["search"] = searchterm
    search_results = search_function(searchterm, **kwargs)
    if search_results is None:
        search_results = []

    options_list = _list_to_options_js(search_results)
    st.session_state[key]["options_js"] = options_list
    return True
Interaction = Literal["submit", "search", "reset", "button-click", "header-click", "footer-click"]
def process_action(props, header: HeaderProps | None, footer: FooterProps | None, interaction: Interaction, value: Any, index: int, valueList: List[Any]) -> bool:
    "..."
    key = props.get("key")
    is_multi = props.get("is_multi")
    # submit, reset and button click are handled JS side.
    if interaction == "search":
        search_function = props.get("search_function")
        if search_function is None:
            print(props)
            raise ValueError(f"Unexpected empty search function for key={key}, index={index}")
        # triggers rerun, no ops afterwards executed
        should_rerun = process_search_simplified(search_function, key, value)
        return should_rerun
    st.session_state[key]["result"] = valueList[index]
    if interaction == "submit":
        st.session_state[key]["search"] = value if not is_multi else ""
    if interaction == "reset":
        default = props.get("default")
        default_options = props.get("default_options", [])
        persistant_default = props.get("persistant_default", False)
        result_val = default if persistant_default else ([] if is_multi else None)
        set_defaults_simplified(key, is_multi, result_val, default_options)
    if interaction == "button-click":
        on_button_click = props.get("on_button_click")
        if on_button_click is None:
            raise ValueError("Can't execute on_button_click event without on_button_click function")
        on_button_click(value, valueList)
    if interaction == "button-click":
        on_button_click = props.get("on_button_click")
        if on_button_click is None:
            raise ValueError("Can't execute on_button_click event without on_button_click function")
        on_button_click(value, valueList)
    if header is not None and interaction == "header-click":
        on_click = header.get("on_click")
        if on_click:
            return on_click(value, valueList)
    if footer is not None and interaction == "footer-click":
        on_click = footer.get("on_click")
        if on_click:
            return on_click(value, valueList)
    return False

async def button_click_handle(props_init, react_state, global_result: Any) -> None:
    """Calls the function which handles the button click for each search widget.
    This is done in a distinct phase (compared to single_state) for passing round the global result as well.
    """
    if react_state is None:
        return
    interaction, value = react_state.get("interaction"), react_state.get("value", None)
    is_change_source = react_state.get("isChangeSource")
    on_button_click = props_init.get("on_button_click")
    if is_change_source and interaction == "button-click" and on_button_click is not None:
        on_button_click(value, global_result)

HeaderProps = TypedDict(
    "HeaderProps",
    {
        "html_str": str,
        "key": str,
        "id_list": List[str], 
        "on_click": Callable[[str, Any], bool]
    },
    total=False,
)
FooterProps = TypedDict(
    "FooterProps",
    {
        "html_str": str,
        "key": str,
        "id_list": List[str], 
        "on_click": Callable[[str, Any], bool]
    },
    total=False,
)

def st_searchbox_list(
    global_key: str,
    props_list: List[Union[SearchboxProps, DatetimepickerProps]],
    global_css_prefix: str | None = None,
    global_css: str | None = None,
    header: HeaderProps | None = None,
    footer: FooterProps | None = None,
    debug_log: bool = False,
    **kwargs,
) -> List[Any]:
    """
    Create a list of searchbox instance, that provides suggestions based on the user input
    and returns a selected option or empty string if nothing was selected

    props_list is a list of:
        search_function (Callable[[str], List[any]]):
            Function that is called to fetch new suggestions after user input.
        placeholder (str, optional):
            Label shown in the searchbox. Defaults to "Search ...".
        label (str, optional):
            Label shown above the searchbox. Defaults to None.
        default (any, optional):
            Return value if nothing is selected so far. Defaults to None.
        default_options (List[any], optional):
            Initial list of options. Defaults to None.
        clear_on_submit (bool, optional):
            Remove suggestions on select. Defaults to False.
        rerun_on_update (bool, optional):
            Rerun the streamlit app after each search. Defaults to True.
        edit_after_submit ("disabled", "current", "option", "concat", optional):
            Edit the search term after submit. Defaults to "disabled".
        style_overrides (StyleOverrides, optional):
            CSS styling passed directly to the react components. Defaults to None.
        key (str, optional):
            Streamlit session key. Defaults to "searchbox".

    Returns:
        any: based on user selection
    """
    # initialize with defaults :
    # for props in props_list:
    async def gather_props_list(props) -> Tuple[Any, Any]:
        """Returns props_js, props_py tuple
        """
        key = props.get("key", "searchbox")
        default = props.get("default", None)
        default_options = props.get("default_options", None)
        is_multi = props.get("is_multi", False)
        if key not in st.session_state:
            set_defaults_simplified(key, is_multi, default, default_options)
        is_special_input = props.get("datetimepicker_props")
        if isinstance(is_special_input, dict):
            item = {
                "datetimepicker_props": props.get("datetimepicker_props", {}),
                "key": props.get("key"),
                "default": props.get("default"),
                "label": props.get("label"),
                "global_css": props.get("global_css")
                }
            return (item, item)
        else:
            raw_selected_value = st.session_state[key]["result"]
            selected_value = None 
            selected_value_list = [] 
            if not is_multi and raw_selected_value is not None:
                selected_value = {
                    "label": raw_selected_value,
                    "value": raw_selected_value
                    }
            if is_multi and isinstance(raw_selected_value, list):
                selected_value_list = [{
                    "label": r,
                    "value": r
                    } for r in raw_selected_value]
            item = {
                "placeholder": props.get("placeholder", "Search ..."),
                "label": props.get("label", None),
                "title": props.get("title", None),
                "title_picto": props.get("title_picto", None),
                "button": props.get("button", None),
                "button_picto": props.get("button_picto", None),
                "css_prefix": props.get("css_prefix", None),
                "search_box_css": props.get("search_box_css", None),
                "default": default,
                "persistant_default": props.get("persistant_default", False),
                "default_options": _list_to_options_js(default_options),
                "clear_on_submit": props.get("clear_on_submit", False),
                "rerun_on_update": props.get("rerun_on_update", True),
                "debounce": props.get("debounce", 100),
                "edit_after_submit": props.get("edit_after_submit", "disabled"),
                "style_overrides": props.get("style_overrides", None),
                "is_multi": is_multi,
                "key": st.session_state[key]["key_react"],
                "options": st.session_state[key]["options_js"],
                "option_source": st.session_state[key]["search"],
                "selected_value": selected_value,
                "selected_value_list": selected_value_list
            }
            item_for_y = {
                **item,
                "key": key,
                "search_function": props.get("search_function"),
                "on_button_click": props.get("on_button_click", None)
            }
            return (item, item_for_y)

    result = []

    async def global_exec():
        tasks = [gather_props_list(props) for props in props_list]
        props_list_zipped = await asyncio.gather(*tasks)
        props_js = [props_js for (props_js, _) in props_list_zipped]
        # everything here is passed to react as this.props.args
        react_state_global = _get_react_component(
            key=global_key, #st.session_state[key]["key_react"],
            propsList=props_js,
            header={
                "html_str": header.get("html_str", ""),
                "key": header.get("key", None),
                "id_list": header.get("id_list", None),
                } if header is not None else None,
            footer={
                "html_str": footer.get("html_str", ""),
                "key": footer.get("key", None),
                "id_list": footer.get("id_list", None),
                } if footer is not None else None,
            css_prefix=global_css_prefix,
            global_css=global_css,
            debug_log=debug_log
        )
        if react_state_global is None:
            return
        action = react_state_global.get("action", {})
        valueList = react_state_global.get("valueList", [])
        if action is None:
            return valueList
        index = action.get("index")
        interaction = action.get("interaction")
        value = action.get("value")
        (_, props) = props_list_zipped[index]
        global_rerun_on_update = process_action(props, header, footer, interaction, value, index, valueList)
        if global_rerun_on_update:
            rerun()
    
    asyncio.run(global_exec())


    # no new react interaction happened
    return result

def get_or_create_eventloop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError as ex:
        if "There is no current event loop in thread" in str(ex):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
