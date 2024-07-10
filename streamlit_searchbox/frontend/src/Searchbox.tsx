import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection,
} from "streamlit-component-lib";
import React, { ReactNode, useCallback, useState } from "react";

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
  interaction: "submit" | "search" | "reset" | "button-click";
  value: any;
  isChangeSource?: boolean
}
const Input = (props: any) => <components.Input {...props} isHidden={false} />;

// export function streamlitReturn(interaction: string, value: any): void {
//   Streamlit.setComponentValue({
//     interaction: interaction,
//     value: value,
//   } as StreamlitReturn);
// }

class SingleSearchBox extends React.Component<{theme: any, args: any, streamlitReturnFn: (interaction: string, value: any) => void}, State> {
  public state: State = {
    menu: false,
    selectedOption: null,
    selectedOptionList: [],
    inputValue: this.props.args.optionSource,
  };

  private style = new SearchboxStyle(
    this.props.theme,
    this.props.args.style_overrides?.searchbox || {},
    this.props.args.style_overrides || {}
  );
  private ref: any = React.createRef();
  /**
   * The last event fired, before any processing whatsoever.
   */
  private eventFired = React.createRef() as React.MutableRefObject<StreamlitReturn["interaction"] | undefined>

  /**
   * Number is the timeoutID, to cancel it if need be.
   */
  private lastSearchUpdate: any = React.createRef<{
    value: string,
    timeout: {
      id: number,
      createdAt: number
    }
  } | undefined>();

  /**
   * new keystroke on searchbox
   * @param input
   * @param _
   * @returns
   */
  private callbackSearch = (input: string): void => {

    const now = Date.now()
    const newValue = {
      value: input,
      timeout: (undefined as any)
    }
    const debounce = this.props.args.debounce
    let resetTimeout = true
    if (this.lastSearchUpdate.current) {
      const {timeout} = this.lastSearchUpdate.current
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
          this.props.streamlitReturnFn("search", this.lastSearchUpdate.current?.value);
        }, debounce)
      }
    }
    this.lastSearchUpdate.current = newValue
    this.setState((s) => ({
      inputValue: input,
      selectedOption: null,
      selectedOptionList: s.selectedOptionList,
    }));
  };

  /**
   * reset button was clicked
   */
  private callbackReset(): void {
    this.setState({
      menu: false,
      selectedOption: null,
      selectedOptionList: [],
      inputValue: "",
    });

    this.props.streamlitReturnFn("reset", "");
  }

  /**
   * submitted selection, clear optionally
   * @param option
   */
  private callbackSubmit(option: Option) {
    this.setState((s, props) => {
      if (this.props.args.isMulti) {
        this.props.streamlitReturnFn("submit", (option as any as Option[]).map(({label}) => label));
      } else {
        this.props.streamlitReturnFn("submit", option.value);
      }
      if (props.args.clear_on_submit) {
        return ({
          menu: false,
          inputValue: "",
          selectedOption: null,
          selectedOptionList: [],
        });
      } else {
        let input = "";

        switch (props.args.edit_after_submit) {
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
        menu: false,
        selectedOption: option,
        inputValue: input,
        selectedOptionList: this.props.args.isMulti ? (option as any as Option[]) : s.selectedOptionList,
      }
      }
    });
  }

  /**
   * show searchbox with label on top
   * @returns
   */
  public render = (): ReactNode => {
    const editableAfterSubmit =
      this.props.args.edit_after_submit !== "disabled";

    // always focus the input field to enable edits
    const onFocus = () => {
      if (this.state.inputValue) {
        if (editableAfterSubmit) {
          this.state.inputValue && this.ref?.current?.select?.inputRef?.select?.();
        }

        this.props.streamlitReturnFn("search", this.state.inputValue)
        this.eventFired.current = "search"
        // hack for the absence of promise in streamlitReturnFn
        waitUntil(() => this.props.args.optionSource === this.state.inputValue, 100).then(() => {
          this.setState({ menu: true })
        })

      }
    };
    const cssPrefix = this.props.args.cssPrefix
    const isLoading = this.eventFired.current === "search"
      && this.props.args.optionSource !== this.state.inputValue
    const optionList = this.props.args.options
    const isMulti = this.props.args.isMulti
    return (
      <>
      {this.props.args.searchBoxCss &&
        <style>
          {this.props.args.searchBoxCss} 
        </style>
      }
      <div className={`${cssPrefix} searchBoxContainer`}>
        {this.props.args.title && (
          <h1 className={`${cssPrefix} title`}>
            {this.props.args.titlePicto &&
              <span
                id={`${cssPrefix} titlePicto`}
                dangerouslySetInnerHTML={{__html: this.props.args.titlePicto}}
              />
            }
            {this.props.args.title}
          </h1>
        )}
        {this.props.args.label && (
          <div className={`${cssPrefix} label`} style={this.style.label}>{this.props.args.label}</div>
        )}
        <div className={`${cssPrefix} buttonRow`}>
          <Select
            // showing the disabled react-select leads to the component
            // not showing the inputValue but just an empty input field
            // we therefore need to re-render the component if we want to keep the focus
            value={isMulti ? this.state.selectedOptionList : this.state.selectedOption}
            inputValue={editableAfterSubmit ? this.state.inputValue : undefined}
            isClearable={true}
            isSearchable={true}
            styles={this.style.select}
            options={optionList}
            placeholder={this.props.args.placeholder}
            isMulti={isMulti}
            // component overrides
            components={{
              // MultiValue
              // MultiValueContainer
              // MultiValueLabel
              // MultiValueRemove
              ClearIndicator: (props) =>
                this.style.clearIndicator(
                  props,
                  this.props.args.style_overrides?.clear || {},
                ),
              DropdownIndicator: () =>
                this.style.iconDropdown(
                  this.state.menu,
                  this.props.args.style_overrides?.dropdown || {},
                ),
              IndicatorSeparator: () => null,
              Input: editableAfterSubmit ? Input : components.Input,
            }}
            // handlers
            filterOption={(_, __) => true}
            onFocus={() => onFocus()}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            onChange={(option: any, a: any) => {
              switch (a.action) {
                case "select-option":
                  this.eventFired.current = "submit"
                  this.callbackSubmit(option);
                  return;
                case "remove-value":
                  if (!this.props.args.isMulti) return
                  this.eventFired.current = "submit"
                  this.callbackSubmit(option);
                  return;

                case "clear":
                  this.eventFired.current = "reset"
                  this.callbackReset();
                  return;
              }
            }}
            onInputChange={(
              inputValue: string,
              { action, prevInputValue }: InputActionMeta,
            ) => {
              switch (action) {
                // ignore menu close or blur/unfocus events
                case "input-change":
                  this.eventFired.current = "search"
                  this.callbackSearch(inputValue);
                  return;
              }
            }}
            onMenuOpen={() => this.setState({ menu: true })}
            onMenuClose={() => this.setState({ menu: false })}
            isLoading={isLoading}
            menuIsOpen={this.props.args.options && this.state.menu}
          />
          {this.props.args.button && (
            <button
              className={`${cssPrefix} button`}
              onClick={() => {
                this.eventFired.current = "button-click"
                this.props.streamlitReturnFn("button-click", this.state.selectedOption?.label)
              }
              }
              >
              {this.props.args.buttonPicto &&
                <span
                  className={`${cssPrefix} buttonPicto`}
                  dangerouslySetInnerHTML={{__html: this.props.args.buttonPicto}}
                />
              }
              {this.props.args.button}
            </button>
          )}
        </div>
      </div>
      </>
    );
  };
}

class Searchbox extends StreamlitComponentBase<(null | StreamlitReturn)[]> {
  state = this.props.args.propsList.map(() => null)
  /**
   * Render any nuber of searchbox
   * @returns
   */
  public render = (): ReactNode => {
    const propsList = this.props.args.propsList
    // const [_, setReturnValues] = useState<(null | StreamlitReturn)[]>(propsList.map(() => null))
    
    const streamlitReturnGlobalFn = (index: number, returnVal: {interaction: any, value: any}): void => {
      this.setState((s: (null | StreamlitReturn)[]) => {
        // This workaround is made because streamlit has sa very weird tendency to turn
        // JS arrays into integer-indexed objects, with all the problems it brings.
        // This way we always have an array to work with (and always in sync with the widget number)
        const newState = this.props.args.propsList.map((_v: any, innerIndex: number) => {
          const value = s?.[innerIndex]
          if (value?.isChangeSource) {
            value.isChangeSource = false
          }
          if (innerIndex === index) {
            return {
              ...returnVal,
              isChangeSource: true
            }
          }
          return value
        })
        Streamlit.setComponentValue(newState);
        return newState
      })
    }

    return <div className={`${this.props.args.cssPrefix ?? 'searchBox'} globalContainer`}>
      {this.props.args.globalCss &&
        <style>
          {this.props.args.globalCss} 
        </style>
      }
      {propsList.map((innerProps: any, index: number) => {
        const streamlitReturnFn = (interaction: string, value: any) => {
          streamlitReturnGlobalFn(index, {interaction, value})
        }
        return <SingleSearchBox
          key={innerProps.key}
          args={innerProps}
          theme={this.props.theme}
          streamlitReturnFn={streamlitReturnFn}
          />
      })}
    </div>
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