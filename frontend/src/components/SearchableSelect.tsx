import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";
import FormField from "./FormField";

interface SearchableSelectProps<T extends string> {
  id: string;
  label: string;
  options: readonly T[];
  value: T | ""; // "" means nothing is selected
  onChange: (value: T | "") => void;
  required?: boolean;
  hint?: string;
  error?: string;
  placeholder?: string;
  noResultsText?: string;
}

// "T extends string" lets this component work with any list of text options,
// and keeps the exact type (for example Department) in value and onChange.
function SearchableSelect<T extends string>({
  id,
  label,
  options,
  value,
  onChange,
  required = false,
  hint,
  error,
  placeholder = "Type to search",
  noResultsText = "No matching options.",
}: SearchableSelectProps<T>) {
  // The text shown in the box. It equals the selected option unless the
  // user is typing a search.
  const [query, setQuery] = useState<string>(value);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const listboxId = `${id}-listbox`;

  // Keep the text in sync when the value is changed from outside
  // (for example when the edit form is pre-filled).
  useEffect(() => {
    setQuery(value);
  }, [value]);

  // When the text still equals the selected option (or is empty), show every
  // option. Otherwise filter by what the user typed.
  const searchText = query.trim().toLowerCase();
  const showAllOptions = searchText === "" || query === value;
  const filteredOptions: readonly T[] = showAllOptions
    ? options
    : options.filter((option) => option.toLowerCase().includes(searchText));

  const hasOptions = filteredOptions.length > 0;
  const safeActiveIndex = hasOptions
    ? Math.min(activeIndex, filteredOptions.length - 1)
    : -1;

  // Scroll the highlighted option into view while navigating with the keyboard.
  useEffect(() => {
    if (!isOpen || safeActiveIndex < 0) {
      return;
    }
    document
      .getElementById(`${id}-option-${safeActiveIndex}`)
      ?.scrollIntoView({ block: "nearest" });
  }, [id, isOpen, safeActiveIndex]);

  function openList() {
    if (isOpen) {
      return;
    }
    const selectedIndex = options.findIndex((option) => option === value);
    setActiveIndex(selectedIndex >= 0 ? selectedIndex : 0);
    setIsOpen(true);
  }

  function selectOption(option: T) {
    onChange(option);
    setQuery(option);
    setIsOpen(false);
  }

  function clearSelection() {
    onChange("");
    setQuery("");
    setIsOpen(false);
    inputRef.current?.focus();
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    setQuery(event.target.value);
    setActiveIndex(0);
    setIsOpen(true);
  }

  function handleBlur() {
    setIsOpen(false);
    if (query.trim() === "" && value !== "") {
      // The user erased the text, so the selection is cleared too.
      onChange("");
    } else {
      // Discard unfinished typing and show the selected option again.
      setQuery(value);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        if (!isOpen) {
          openList();
        } else if (hasOptions) {
          setActiveIndex((safeActiveIndex + 1) % filteredOptions.length);
        }
        break;

      case "ArrowUp":
        event.preventDefault();
        if (!isOpen) {
          openList();
        } else if (hasOptions) {
          setActiveIndex(
            (safeActiveIndex - 1 + filteredOptions.length) % filteredOptions.length
          );
        }
        break;

      case "Enter":
        // While the list is open, Enter chooses an option instead of
        // submitting the whole form.
        if (isOpen) {
          event.preventDefault();
          if (safeActiveIndex >= 0) {
            selectOption(filteredOptions[safeActiveIndex]);
          }
        }
        break;

      case "Escape":
        if (isOpen) {
          event.preventDefault();
          setIsOpen(false);
          setQuery(value);
        }
        break;

      default:
        break;
    }
  }

  return (
    <FormField
      id={id}
      label={label}
      required={required}
      hint={hint}
      error={error}
    >
      {(control) => (
        <div className="combobox">
          <input
            {...control}
            ref={inputRef}
            type="text"
            role="combobox"
            className="form-input combobox-input"
            autoComplete="off"
            placeholder={placeholder}
            value={query}
            aria-expanded={isOpen}
            aria-autocomplete="list"
            aria-controls={isOpen && hasOptions ? listboxId : undefined}
            aria-activedescendant={
              isOpen && safeActiveIndex >= 0
                ? `${id}-option-${safeActiveIndex}`
                : undefined
            }
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onClick={openList}
            onFocus={(event) => event.currentTarget.select()}
            onBlur={handleBlur}
          />

          <div className="combobox-actions">
            {value !== "" && (
              <button
                type="button"
                className="combobox-clear"
                aria-label={`Clear ${label}`}
                onMouseDown={(event) => event.preventDefault()}
                onClick={clearSelection}
              >
                &times;
              </button>
            )}
            <span className="combobox-chevron" aria-hidden="true"></span>
          </div>

          {isOpen && hasOptions && (
            <ul
              id={listboxId}
              role="listbox"
              aria-label={label}
              className="combobox-listbox"
              // Keeps the focus in the text box when an option is clicked.
              onMouseDown={(event) => event.preventDefault()}
            >
              {filteredOptions.map((option, index) => (
                <li
                  key={option}
                  id={`${id}-option-${index}`}
                  role="option"
                  aria-selected={option === value}
                  className={
                    index === safeActiveIndex
                      ? "combobox-option is-active"
                      : "combobox-option"
                  }
                  onClick={() => selectOption(option)}
                  onMouseEnter={() => setActiveIndex(index)}
                >
                  {option}
                </li>
              ))}
            </ul>
          )}

          {isOpen && !hasOptions && (
            <div className="combobox-listbox">
              <p className="combobox-empty">{noResultsText}</p>
            </div>
          )}

          {/* Announced by screen readers when the list changes */}
          <div className="visually-hidden" role="status" aria-live="polite">
            {isOpen
              ? hasOptions
                ? `${filteredOptions.length} options available. Use the up and down arrow keys to review them.`
                : noResultsText
              : ""}
          </div>
        </div>
      )}
    </FormField>
  );
}

export default SearchableSelect;