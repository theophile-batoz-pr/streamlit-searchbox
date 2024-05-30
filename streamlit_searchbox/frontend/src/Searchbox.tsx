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
  option: Option | null;
  inputValue: string;
}

interface StreamlitReturn {
  interaction: "submit" | "search" | "reset" | "button-click";
  value: any;
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
    option: null,
    inputValue: "",
  };

  private style = new SearchboxStyle(
    this.props.theme,
    this.props.args.style_overrides?.searchbox || {},
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
    this.setState({
      inputValue: input,
      option: null,
    });

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
  };

  /**
   * reset button was clicked
   */
  private callbackReset(): void {
    this.setState({
      menu: false,
      option: null,
      inputValue: "",
    });

    this.props.streamlitReturnFn("reset", null);
  }

  /**
   * submitted selection, clear optionally
   * @param option
   */
  private callbackSubmit(option: Option) {
    if (this.props.args.clear_on_submit) {
      this.setState({
        menu: false,
        inputValue: "",
        option: null,
      });
    } else {
      let input = "";

      switch (this.props.args.edit_after_submit) {
        case "current":
          input = this.state.inputValue;
          break;

        case "option":
          input = option.label;
          break;

        case "concat":
          input = this.state.inputValue + " " + option.label;
          break;
      }

      this.setState({
        menu: false,
        option: option,
        inputValue: input,
      });
    }

    this.props.streamlitReturnFn("submit", option.value);
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
        this.setState({ menu: true })
        this.props.streamlitReturnFn("search", this.state.inputValue)
      }
    };
    const cssPrefix = this.props.args.cssPrefix
    const isLoading = this.eventFired.current === "search"
      && this.props.args.optionSource !== this.state.inputValue
    const optionList = this.eventFired.current !== "reset"
      && this.props.args.optionSource === this.state.inputValue ?
        this.props.args.options : []
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
            value={this.state.option}
            inputValue={editableAfterSubmit ? this.state.inputValue : undefined}
            isClearable={true}
            isSearchable={true}
            styles={this.style.select}
            options={optionList}
            placeholder={this.props.args.placeholder}
            // component overrides
            components={{

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
                this.state.option?.value && this.props.streamlitReturnFn("button-click", this.state.option?.value)
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
    
    const streamlitReturnGlobalFn = (index: number, returnVal: any): void => {
      this.setState((s: (null | StreamlitReturn)[]) => {
        s[index] = returnVal;
        Streamlit.setComponentValue(s);
        return s
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
