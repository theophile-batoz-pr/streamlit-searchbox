import {
  Streamlit,
  StreamlitComponentBase,
  Theme,
  withStreamlitConnection,
} from "streamlit-component-lib";
import React, { ReactNode, useCallback, useMemo, useState } from "react";

import SearchboxStyle from "./styling";
import Select, { InputActionMeta, components } from "react-select";

type Option = {
  value: string;
  label: string;
};

interface State {
  menu: boolean;
  selectedOption: Option | null;
  selectedOptionList: Option[];
  inputValue: string;
}

interface StreamlitReturn {
  interaction: "submit" | "search" | "reset" | "button-click" | "simple-value"
  value: any
  index: number
  isChangeSource?: boolean
}
type StreamlitFnType = (interaction: StreamlitReturn["interaction"], value: any) => void

const Input = (props: any) => <components.Input {...props} isHidden={false} />;

function SingleSearchBox(props: {theme: any, args: any, streamlitReturnFn: StreamlitFnType}) {

  const args = props.args
  const streamlitReturnFn = props.streamlitReturnFn
  const {
    option_source,
    css_prefix,
    default_options,
    options,
    is_multi,
    search_box_css,
    title,
    title_picto,
    label,
    placeholder,
    edit_after_submit,
    style_overrides,
    clear_on_submit,
    debounce,
    button,
    button_picto,
    selected_value,
    selected_value_list,
  } = args
  const editableAfterSubmit =
    edit_after_submit !== "disabled";
  const [state, setState] = useState<State>(() => ({
    menu: false,
    selectedOption: selected_value,
    selectedOptionList: selected_value_list,
    inputValue: option_source,
  }))
  const style = useMemo(() => new SearchboxStyle(
    props.theme,
    style_overrides?.searchbox || {},
    style_overrides || {}
  ), [props.theme, style_overrides])
  const ref: any = React.createRef();
  const eventFired = React.createRef() as React.MutableRefObject<StreamlitReturn["interaction"] | undefined>
  const lastSearchUpdate: any = React.createRef<{
    value: string,
    timeout: {
      id: number,
      createdAt: number
    }
  } | undefined>();

  const callbackSearch = useCallback((input: string, debounce: number, streamlitReturnFn: StreamlitFnType): void => {

    const now = Date.now()
    const newValue = {
      value: input,
      timeout: (undefined as any)
    }
    let resetTimeout = true
    if (lastSearchUpdate.current) {
      const {timeout} = lastSearchUpdate.current
      const {id, createdAt} = timeout
      newValue.timeout = timeout
      if (now - createdAt > debounce - 10) {
        clearTimeout(id)
      } else {
        resetTimeout = false
      }
    }
    if (resetTimeout) {
      newValue.timeout = {
        createdAt: now,
        id: setTimeout(() => {
          streamlitReturnFn("search", lastSearchUpdate.current?.value);
        }, debounce)
      }
    }
    lastSearchUpdate.current = newValue
    setState((s) => ({
      inputValue: input,
      selectedOption: null,
      selectedOptionList: s.selectedOptionList,
      menu: s.menu
    }));
  }, [lastSearchUpdate])
  const callbackReset = useCallback(() => {
    setState(() => {
      streamlitReturnFn("reset", "");
      return {
        menu: false,
        selectedOption: null,
        selectedOptionList: [],
        inputValue: "",
      }
    });
  }, [streamlitReturnFn])
  const callbackSubmit = useCallback((option: Option) => {
    setState((s) => {
      if (is_multi) {
        streamlitReturnFn("submit", (option as any as Option[]).map(({label}) => label));
      } else {
        streamlitReturnFn("submit", option.label);
      }
      let input = "";

      switch (edit_after_submit) {
        case "current":
          input = s.inputValue;
          break;

        case "option":
          input = option.label;
          break;

        case "concat":
          input = s.inputValue + " " + option.label;
          break;
      }
      return {
        menu: clear_on_submit ? false : true,
        inputValue: clear_on_submit && is_multi ? "" : input,
        selectedOption: option,
        selectedOptionList: is_multi ? (option as any as Option[]) : s.selectedOptionList,
      }
    });
  }, [streamlitReturnFn, is_multi, clear_on_submit, edit_after_submit])
  const openSelectMenu = useCallback(() => setState((s) => ({...s, menu: true })), [])
  const onFocus = useCallback(() => {
    const inputValue = state.inputValue
    if (inputValue) {
      if (editableAfterSubmit) {
        inputValue && ref?.current?.select?.inputRef?.select?.();
      }

      streamlitReturnFn("search", inputValue)
      eventFired.current = "search"
      // hack for the absence of promise in streamlitReturnFn
      waitUntil(() => option_source === inputValue, 100).then(() => {
        openSelectMenu()
      })
    }
  }, [option_source, eventFired, state.inputValue, streamlitReturnFn, editableAfterSubmit, openSelectMenu, ref])
  const isLoading = eventFired.current === "search"
    && option_source !== state.inputValue
  const optionList = state.inputValue === "" ?
    default_options
    : options
  const onSelectChange = useCallback((option: any, a: any) => {
    switch (a.action) {
      case "select-option":
        eventFired.current = "submit"
        callbackSubmit(option);
        return;
      case "remove-value":
        if (!is_multi) return
        eventFired.current = "submit"
        callbackSubmit(option);
        return;

      case "clear":
        eventFired.current = "reset"
        callbackReset();
        return;
    }
  }, [is_multi, eventFired, callbackReset, callbackSubmit])
  const onSelectInputChange = useCallback((
    inputValue: string,
    { action, prevInputValue }: InputActionMeta,
  ) => {
    switch (action) {
      // ignore menu close or blur/unfocus events
      case "input-change":
        eventFired.current = "search"
        callbackSearch(inputValue, debounce, streamlitReturnFn);
        return;
    }
  }, [debounce, streamlitReturnFn, eventFired, callbackSearch])
  const selectComponents = useMemo(() => ({
    // MultiValue
    // MultiValueContainer
    // MultiValueLabel
    // MultiValueRemove
    ClearIndicator: (props: any) =>
      style.clearIndicator(
        props,
        style_overrides?.clear || {},
      ),
    DropdownIndicator: () =>
      style.iconDropdown(
        state.menu,
        style_overrides?.dropdown || {},
      ),
    IndicatorSeparator: () => null,
    Input: editableAfterSubmit ? Input : components.Input,
  }), [style_overrides?.clear, style_overrides?.dropdown, editableAfterSubmit, state.menu, style])
  const onButtonClick = useCallback(() => {
    eventFired.current = "button-click"
    streamlitReturnFn("button-click", state.selectedOption?.label)
  }, [streamlitReturnFn, state.selectedOption?.label, eventFired])
  return (
    <>
    {search_box_css &&
      <style>
        {search_box_css} 
      </style>
    }
    <div className={`${css_prefix} searchBoxContainer`}>
      {title && (
        <h1 className={`${css_prefix} title`}>
          {title_picto &&
            <span
              id={`${css_prefix} title_picto`}
              dangerouslySetInnerHTML={{__html: title_picto}}
            />
          }
          {title}
        </h1>
      )}
      {label && (
        <div className={`${css_prefix} label`} style={style.label}>{label}</div>
      )}
      <div className={`${css_prefix} buttonRow`}>
        <Select
          // showing the disabled react-select leads to the component
          // not showing the inputValue but just an empty input field
          // we therefore need to re-render the component if we want to keep the focus
          value={is_multi ? state.selectedOptionList : state.selectedOption}
          inputValue={editableAfterSubmit ? state.inputValue : undefined}
          isClearable={true}
          isSearchable={true}
          styles={style.select}
          options={optionList}
          placeholder={placeholder}
          isMulti={is_multi}
          // component overrides
          components={selectComponents}
          // handlers
          filterOption={(_, __) => true}
          onFocus={onFocus}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          onChange={onSelectChange}
          onInputChange={onSelectInputChange}
          onMenuOpen={openSelectMenu}
          onMenuClose={useCallback(() => setState((s) => ({...s, menu: false })), [])}
          isLoading={isLoading}
          menuIsOpen={optionList && state.menu}
        />
        {button && (
          <button
            className={`${css_prefix} button`}
            onClick={onButtonClick}
            >
            {button_picto &&
              <span
                className={`${css_prefix} button_picto`}
                dangerouslySetInnerHTML={{__html: button_picto}}
              />
            }
            {button}
          </button>
        )}
      </div>
    </div>
    </>
  );
}

function SearchBoxFnRenderer({theme, streamlitReturnGlobalFn, innerProps, index} : {theme: any, streamlitReturnGlobalFn: any, innerProps: any, index: number}) {
    const streamlitReturnFn = useCallback((interaction: string, value: any) => {
      streamlitReturnGlobalFn({index, interaction, value})
    }, [index, streamlitReturnGlobalFn])
    if (innerProps.datetimepicker_props) {
      const datetimepickerId = `input-dtpck-${innerProps.key}`
      const css_prefix = innerProps.css_prefix
      return <SimpleDatetimePicker
        defaultVal={innerProps.default as string}
        css_prefix={css_prefix}
        innerProps={innerProps}
        datetimepickerId={datetimepickerId}
        streamlitReturnFn={streamlitReturnFn}
        />
    }
    return <SingleSearchBox
      key={innerProps.key}
      args={innerProps}
      theme={theme}
      streamlitReturnFn={streamlitReturnFn}
      />
}

type Args = {
  css_prefix: string,
  global_css: string,
  header?: {
    html_str: string
  },
  footer?: {
    html_str: string
  },
  propsList: any[],
  button: string,
  button_picto: string 
}
type GlobalState = {
  action: null | StreamlitReturn,
  valueList: (string | string[] | null)[]
}
function SearchBoxFn(props: {theme?: Theme | undefined, args: Args, debug_log?: boolean}) {
  const debugLog = props.debug_log
  const args = props.args
  const propsList = args.propsList
  const [_state, setState] = useState<GlobalState>(() => ({
    action: null,
    valueList: propsList.map((props) => props.default ?? null)
  }))
  const streamlitReturnGlobalFn = useCallback((input: {interaction: any, value: any, index: number}): void => {
    setState((s: GlobalState) => {
      const newState = {
        action: input,
        valueList: s.valueList
      }
      if (input.interaction === "submit" || input.interaction === "simple-value") {
        const newValueList = [...s.valueList]
        newValueList[input.index] = input.value
        newState.valueList = newValueList
      } else if (input.interaction === "reset") {
        const newValueList = [...s.valueList]
        newValueList[input.index] = newValueList[input.index]?.length ? [] : null
        newState.valueList = newValueList
      }
      debugLog && console.log("newState", newState)
      Streamlit.setComponentValue(newState);
      return newState
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...propsList, Streamlit.setComponentValue, debugLog])
  const onHeaderClick = useCallback((e) => {
    return streamlitReturnGlobalFn({
      interaction: "header-click",
      value: e?.target?.id,
      index: -1
    })
  }, [streamlitReturnGlobalFn])
  const onFooterClick = useCallback((e) => {
    return streamlitReturnGlobalFn({
      interaction: "footer-click",
      value: e?.target?.id,
      index: -1
    })
  }, [streamlitReturnGlobalFn])
  const {
    css_prefix,
    global_css,
    header,
    footer
    // button,
    // button_picto
  } = args
  return <div className={`${css_prefix ?? 'searchBox'} globalContainer`}>
    {global_css &&
      <style>
        {global_css} 
      </style>
    }
    {
      header &&
      <div
        className={`${css_prefix} globalframe header`}
        dangerouslySetInnerHTML={{__html: header.html_str}}
        onClick={onHeaderClick}
      />
    }
    {propsList.map((innerProps: any, index: number) => {
      return <SearchBoxFnRenderer
        key={innerProps.key}
        index={index}
        streamlitReturnGlobalFn={streamlitReturnGlobalFn}
        innerProps={innerProps}
        theme={props.theme}
        />
    })}
    {
      footer &&
      <div
        className={`${css_prefix} globalframe footer`}
        dangerouslySetInnerHTML={{__html: footer.html_str}}
        onClick={onFooterClick}
      />
    }
  </div>
}

class Searchbox extends StreamlitComponentBase<(null | StreamlitReturn)[]> {
  /**
   * Render any nuber of searchbox
   * @returns
   */
  public render = (): ReactNode => {
    return <SearchBoxFn {...this.props} />
    
  }
}
export default withStreamlitConnection(Searchbox);


function waitUntil (check: () => boolean, baseMs: number = 10): Promise<void> {
  return new Promise((res, reject) => {
    setTimeout(() => {
      if (check()) {
        res(undefined)
      } else {
        waitUntil(check, baseMs)
      }
    }, baseMs)
  })
}


function SimpleDatetimePicker({defaultVal, css_prefix, innerProps, datetimepickerId, streamlitReturnFn}: {
  defaultVal: string;
  css_prefix: string;
  innerProps: any;
  datetimepickerId: string;
  streamlitReturnFn: ((a: string, e: any) => any);
}) {
  const [value, setValue] = useState(defaultVal)
  return <div className={`${css_prefix} datetimePickerContainer`}>
    <label className={`${css_prefix} label`} >
      {innerProps.label}
    </label>
    <input
      id={datetimepickerId}
      className={`${css_prefix} datetimePicker`}
      {...innerProps.datetimepicker_props}
      value={value}
      onChange={useCallback((e) => {
        setValue(e.target.value)
        return streamlitReturnFn("simple-value", e.target.value)
      }, [streamlitReturnFn])}
    />
  </div>
}