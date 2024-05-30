"""
module for streamlit searchbox component
"""

from __future__ import annotations

import functools
import logging
import os
import time
from typing import Any, Callable, List, Literal, TypedDict, TypeVar, Generic

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
    return [
        {
            "label": str(v[0]) if isinstance(v, tuple) else str(v),
            "value": i,
        }
        for i, v in enumerate(options)
    ]


def _process_search(
    search_function: Callable[[str], List[Any]],
    key: str,
    searchterm: str,
    rerun_on_update: bool,
    **kwargs,
) -> None:
    # nothing changed, avoid new search
    if searchterm == st.session_state[key]["search"]:
        return st.session_state[key]["result"]

    st.session_state[key]["search"] = searchterm
    search_results = search_function(searchterm, **kwargs)

    if search_results is None:
        search_results = []

    st.session_state[key]["options_js"] = _list_to_options_js(search_results)
    st.session_state[key]["options_py"] = _list_to_options_py(search_results)

    if rerun_on_update:
        rerun()


def _set_defaults(
    key: str,
    default: Any,
    default_options: List[Any] | None = None,
) -> None:
    st.session_state[key] = {
        # updated after each selection / reset
        "result": default,
        # updated after each search keystroke
        "search": "",
        # updated after each search_function run
        "options_js": [],
        # key that is used by react component, use time suffix to reload after clear
        "key_react": f"{key}_react_{str(time.time())}",
    }

    if default_options:
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
    cssPrefix: str | None = None,
    globalCss: str | None = None,
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
        _set_defaults(key, default, default_options)

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
            "cssPrefix": cssPrefix,
            "globalCss": globalCss,
            # react return state within streamlit session_state
            "key": st.session_state[key]["key_react"],
        }]
    )

    if react_state is None:
        return st.session_state[key]["result"]
    else:
        react_state = react_state[0]
    interaction, value = react_state["interaction"], react_state["value"]

    if interaction == "search":
        # triggers rerun, no ops afterwards executed
        _process_search(search_function, key, value, rerun_on_update, **kwargs)

    if interaction == "button-click" and on_button_click is not None:
        on_button_click(value)

    if interaction == "submit":
        st.session_state[key]["result"] = (
            st.session_state[key]["options_py"][value]
            if "options_py" in st.session_state[key]
            else value
        )
        return st.session_state[key]["result"]

    if interaction == "reset":
        _set_defaults(key, default, default_options)

        if rerun_on_update:
            rerun()

        return default

    # no new react interaction happened
    return st.session_state[key]["result"]

SearchboxProps = TypedDict(
    "SearchboxProps",
    {
        "search_function": Callable[[str], List[Any]],
        "placeholder": str,
        "label": str | None,
        "title": str | None,
        "button": str | None,
        "cssPrefix": str | None,
        "globalCss": str | None,
        "on_button_click": Callable[[str], None] | None,
        "default": Any,
        "default_options": List[Any] | None,
        "clear_on_submit": bool,
        "rerun_on_update": bool,
        "debounce": int,
        "edit_after_submit": Literal["disabled", "current", "option", "concat"],
        "style_overrides": StyleOverrides | None,
        "key": str,
    },
    total=False,
)

@wrap_inactive_session
def st_searchbox_list(
    global_key: str,
    props_list: List[SearchboxProps],
    **kwargs,
) -> Any:
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
    props_list_initialized = []
    props_list_serializable = []
    # initialize with defaults :
    for props in props_list:
        key = props.get("key", "searchbox")
        default = props.get("default", None)
        default_options = props.get("default_options", None)
        item = {
            "placeholder": props.get("placeholder", "Search ..."),
            "label": props.get("label", None),
            "title": props.get("title", None),
            "button": props.get("button", None),
            "cssPrefix": props.get("cssPrefix", None),
            "globalCss": props.get("globalCss", None),
            "default": default,
            "default_options": default_options,
            "clear_on_submit": props.get("clear_on_submit", False),
            "rerun_on_update": props.get("rerun_on_update", True),
            "debounce": props.get("debounce", 100),
            "edit_after_submit": props.get("edit_after_submit", "disabled"),
            "style_overrides": props.get("style_overrides", None),
            "key": key,
        }
        props_list_serializable.append(item)
        item_full = {
            **item,
            "search_function": props.get("search_function"),
            "on_button_click": props.get("on_button_click", None)
        }
        props_list_initialized.append(item_full)
        if key not in st.session_state:
            _set_defaults(key, default, default_options)

    # everything here is passed to react as this.props.args
    react_state_global = _get_react_component(
        key=global_key, #st.session_state[key]["key_react"],
        propsList=props_list_serializable
    )
    print(react_state_global)
    def single_state(props_init, react_state):
        "We assume the input props and the result are array of the same size (should always be the case)."
        if react_state is None:
            return st.session_state[key]["result"]
        search_function = props_init.get("search_function")
        rerun_on_update = props_init.get("rerun_on_update")
        on_button_click = props_init.get("on_button_click")
        interaction, value = react_state["interaction"], react_state["value"]

        if interaction == "search":
            # triggers rerun, no ops afterwards executed
            _process_search(search_function, key, value, rerun_on_update, **kwargs)

        if interaction == "button-click" and on_button_click is not None:
            on_button_click(value)

        if interaction == "submit":
            st.session_state[key]["result"] = (
                st.session_state[key]["options_py"][value]
                if "options_py" in st.session_state[key]
                else value
            )
            return st.session_state[key]["result"]

        if interaction == "reset":
            _set_defaults(key, default, default_options)

            if rerun_on_update:
                rerun()

            return default

        return st.session_state[key]["result"]
        
    result = [
        single_state(props, react_state_global[idx] if react_state_global is not None else None)
        for idx, props in enumerate(props_list_initialized)]
    # no new react interaction happened
    return result
