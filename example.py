from __future__ import annotations

import enum
import logging
import random
import time
from typing import Any, List

import requests
import streamlit as st

from streamlit_searchbox import st_searchbox, st_searchbox_list

logging.getLogger("streamlit_searchbox").setLevel(logging.DEBUG)

st.set_page_config(layout="centered", page_title="Searchbox Demo")


def search_wikipedia_ids(searchterm: str) -> List[tuple[str, Any]]:
    """
    function with list of tuples (label:str, value:any)
    """
    print("calling", searchterm)
    # you can use a nice default here
    if not searchterm:
        return []

    # search that returns a list of wiki articles in dict form
    # with information on title, id, etc
    response = requests.get(
        "http://en.wikipedia.org/w/api.php",
        params={
            "list": "search",
            "format": "json",
            "action": "query",
            "srlimit": 10,
            "limit": 10,
            "srsearch": searchterm,
        },
        timeout=5,
    ).json()["query"]["search"]

    # first element will be shown in search, second is returned from component
    return [
        (
            str(article["title"]),
            article["pageid"],
        )
        for article in response
        if searchterm in article["title"]
    ]


def search(searchterm: str) -> List[str]:
    return [f"{searchterm}_{i}" for i in range(10)]


def search_rnd_delay(searchterm: str) -> List[str]:
    time.sleep(random.randint(1, 5))
    return [f"{searchterm}_{i}" for i in range(10)]


def search_enum_return(_: str):
    e = enum.Enum("FancyEnum", {"a": 1, "b": 2, "c": 3})
    return [e.a, e.b, e.c]


def search_empty_list(_: str):
    if not st.session_state.get("search_empty_list_n", None):
        st.session_state["search_empty_list_n"] = 1
        return ["a", "b", "c"]

    return []


def search_kwargs(searchterm: str, **kwargs) -> List[str]:
    return [f"{searchterm}_{len(kwargs)}" for i in range(10)]


#################################
#### application starts here ####
#################################


# searchbox configurations, see __init__.py for details
# will pass all kwargs to the searchbox component
boxes = [
    dict(
        search_function=search_wikipedia_ids,
        placeholder="Search Wikipedia",
        label=search_wikipedia_ids.__name__,
        default="SOME DEFAULT",
        clear_on_submit=False,
        key=search_wikipedia_ids.__name__,
        debounce=300,
        edit_after_submit="option",
        title="qsdqd",
        button="qsdqd",
        buttonPicto="""
<svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
<rect x="0.5" y="0.5" width="31" height="31" rx="3.5" fill="#013467" stroke="#013467"/>
<mask id="mask0_971_57732" style="mask-type:alpha" maskUnits="userSpaceOnUse" x="6" y="6" width="20" height="20">
<rect x="6" y="6" width="20" height="20" fill="#D9D9D9"/>
</mask>
<g mask="url(#mask0_971_57732)">
<path d="M16 24.1694C14.8796 24.1694 13.8232 23.9561 12.8311 23.5294C11.8389 23.1028 10.97 22.5166 10.2242 21.7708C9.47843 21.025 8.89306 20.1553 8.46809 19.1615C8.04311 18.1676 7.83063 17.1105 7.83063 15.99C7.83063 14.8557 8.04311 13.7967 8.46809 12.8132C8.89306 11.8296 9.47843 10.9658 10.2242 10.2217C10.97 9.47757 11.8389 8.89303 12.8311 8.46805C13.8232 8.04308 14.8796 7.8306 16 7.8306C17.1344 7.8306 18.1942 8.04308 19.1794 8.46805C20.1646 8.89303 21.0301 9.47757 21.7758 10.2217C22.5216 10.9658 23.107 11.8296 23.532 12.8132C23.9569 13.7967 24.1694 14.8557 24.1694 15.99C24.1694 17.1105 23.9569 18.1676 23.532 19.1615C23.107 20.1553 22.5216 21.025 21.7758 21.7708C21.0301 22.5166 20.1646 23.1028 19.1794 23.5294C18.1942 23.9561 17.1344 24.1694 16 24.1694ZM16 22.4402C16.7373 22.4402 17.4363 22.3235 18.0969 22.0901C18.7576 21.8567 19.3557 21.5261 19.8913 21.0983L10.8918 12.1037C10.4706 12.646 10.1433 13.2458 9.9099 13.9031C9.67651 14.5604 9.55981 15.256 9.55981 15.99C9.55981 17.779 10.1868 19.3012 11.4407 20.5568C12.6946 21.8124 14.2144 22.4402 16 22.4402ZM21.1133 19.8763C21.5311 19.3341 21.8568 18.7343 22.0901 18.077C22.3235 17.4197 22.4402 16.724 22.4402 15.99C22.4402 14.2044 21.8133 12.6863 20.5594 11.4357C19.3054 10.1851 17.7856 9.55978 16 9.55978C15.266 9.55978 14.5712 9.67482 13.9156 9.90489C13.2599 10.135 12.661 10.4589 12.1187 10.8768L21.1133 19.8763Z" fill="white"/>
</g>
</svg>
        """,
        cssPrefix="XXXX",
        rerun_on_update=True,
    ),
    # dict(
    #     search_function=search,
    #     default=None,
    #     label=search.__name__,
    #     clear_on_submit=False,
    #     key=search.__name__,
    # ),
    # dict(
    #     search_function=search_rnd_delay,
    #     default=None,
    #     clear_on_submit=False,
    #     label=search_rnd_delay.__name__,
    #     key=search_rnd_delay.__name__,
    # ),
    # dict(
    #     search_function=search_enum_return,
    #     clear_on_submit=True,
    #     key=search_enum_return.__name__,
    #     label=search_enum_return.__name__,
    # ),
    # dict(
    #     search_function=search_empty_list,
    #     clear_on_submit=True,
    #     key=search_empty_list.__name__,
    #     label=search_empty_list.__name__,
    # ),
    # dict(
    #     search_function=search,
    #     default_options=["inital", "list", "of", "options"],
    #     key=f"{search.__name__}_default_options",
    #     label=f"{search.__name__}_default_options",
    #     style_overrides={"clear": {"width": 25, "height": 25}},
    # ),
    # dict(
    #     search_function=search,
    #     default="initial",
    #     default_options=["inital", "list", "of", "options"],
    #     key=f"{search.__name__}_default_options_all",
    #     label=f"{search.__name__}_default_options_all",
    # ),
    # dict(
    #     search_function=search,
    #     default_options=[("inital", "i"), ("list", "l")],
    #     key=f"{search.__name__}_default_options_tuple",
    #     label=f"{search.__name__}_default_options_tuple",
    # ),
    # dict(
    #     search_function=search,
    #     key=f"{search.__name__}_rerun_disabled",
    #     rerun_on_update=False,
    #     label=f"{search.__name__}_rerun_disabled",
    # ),
    # dict(
    #     search_function=search,
    #     key=f"{search.__name__}_edit_current_after_submit",
    #     edit_after_submit="current",
    #     label=f"{search.__name__}_edit_current_after_submit",
    # ),
    # dict(
    #     search_function=search,
    #     key=f"{search.__name__}_edit_option_after_submit",
    #     edit_after_submit="option",
    #     label=f"{search.__name__}_edit_option_after_submit",
    # ),
    # dict(
    #     search_function=search,
    #     key=f"{search.__name__}_edit_concat_after_submit",
    #     edit_after_submit="concat",
    #     label=f"{search.__name__}_edit_concat_after_submit",
    # ),
    # dict(
    #     search_function=search_kwargs,
    #     key=f"{search_kwargs.__name__}_kwargs",
    #     label=f"{search_kwargs.__name__}_kwargs",
    #     a=1,
    #     b=2,
    # ),
    # dict(
    #     search_function=search,
    #     default=None,
    #     label=f"{search.__name__}_override_style",
    #     clear_on_submit=False,
    #     key=f"{search.__name__}_override_style",
    #     style_overrides={
    #         "clear": {
    #             "width": 20,
    #             "height": 20,
    #             "icon": "circle-unfilled",
    #             "stroke-width": 2,
    #             "stroke": "red",
    #         },
    #         "dropdown": {
    #             "rotate": True,
    #             "width": 30,
    #             "height": 30,
    #         },
    #         "searchbox": {
    #             "menuList": {"backgroundColor": "transparent"},
    #             "singleValue": {"color": "red"},
    #             "option": {"color": "blue", "backgroundColor": "yellow"},
    #         },
    #     },
    # ),
]


searchboxes, visual_ref, form_example, manual_example = st.tabs(
    ["Searchboxes", "Visual Reference", "Form Example", "Manual Example"]
)

with searchboxes:
    # iterate over boxes in groups of 3, fit into columns
    for box_l in [boxes[i : i + 2] for i in range(0, len(boxes), 2)]:
        cols = st.columns(2)

        for i, box in enumerate(box_l):
            with cols[i]:
                selected_value = st_searchbox(**box)  # type: ignore

                if selected_value:
                    st.info(f"{selected_value} {type(selected_value)}")

        st.markdown("---")

    st_searchbox(
        search_function=search,
        key=f"{search.__name__}_style_manual",
        style_overrides={
            "clear": {
                "width": 20,
                "height": 20,
                "icon": "circle-unfilled",
                "stroke-width": 2,
                "stroke": "red",
            },
            "dropdown": {
                "rotate": True,
                "width": 30,
                "height": 30,
            },
            "searchbox": {
                "menuList": {"backgroundColor": "transparent"},
                "singleValue": {"color": "red", "some": "data"},
                "option": {"color": "blue", "backgroundColor": "yellow"},
            },
        },
    )


with visual_ref:
    st.multiselect(
        "Multiselect",
        [1, 2, 3, 4, 5],
        default=[1, 2],
        key="multiselect",
    )
    st.selectbox(
        "Selectbox",
        [1, 2, 3],
        index=1,
        key="selectbox",
    )

with form_example:
    with st.form("myform"):
        c1, c2 = st.columns(2)
        with c1:
            sr = st_searchbox(
                search_function=search,
                key=f"{search.__name__}_form",
            )
        with c2:
            st.form_submit_button("load suggestions")

        submit = st.form_submit_button("real submit")
        if submit:
            st.write("form submitted")
            st.write(sr)

with manual_example:
    key = f"{search.__name__}_manual"

    if key in st.session_state:
        st.session_state[key]["options_js"] = [
            {"label": f"{st.session_state[key]['search']}_{i}", "value": i}
            for i in range(5)
        ]
        st.session_state[key]["options_py"] = [i for i in range(5)]

    manual = st_searchbox(
        search_function=lambda _: [],
        key=key,
    )

    st.write(manual)
globalCss="""
        .title {
            color: purple
        }
        .globalContainer {
            # background: #DAE4F4;
            # border: 1px solid rgba(49, 51, 63, 0.2);
            # border-radius: 0.3rem;
            padding: 1em;
            # display: flex;
        }
        .searchBoxContainer {
            background: #DAE4F4;
            border: 1px solid rgba(49, 51, 63, 0.2);
            border-radius: 0.3rem;
            padding: 1em;
            # display: flex;
        }
        .buttonRow {
            # background: white;
            display: flex;
            gap: 1rem;
        }
        .button {
            border: 2px solid #013467;
            color: #013467;
            border-radius: 0.3rem;
            background: white;
            
            &:hover {
                background: #013467;
                color: white;
            }
        }
        """
st_searchbox_list(global_key="lqksjdlkqsjldkj", props_list=[
    {**boxes[0], "key":"okokok-lqjjzbjfkfofof"}, {**boxes[0], "key":"okokok-mlqkjskdkmkqdlmk"
               }], global_css=globalCss)