import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";
import type { SubjectGroup } from "../constants/tutorOptions";
import FormField from "./FormField";

interface MultiSelectProps {
  id: string;
  label: string;
  groups: readonly SubjectGroup[];
  values: string[]; // the selected items
  onChange: (values: string[]) => void;
  required?: boolean;
  hint?: string;
  error?: string;
  placeholder?: string;
  noResultsText?: string;
}

// A group after the search filter and removal of already selected items.
// "startIndex" is the position of its first option in the flat list, which is
// what keyboard navigation moves through.
interface VisibleGroup {
  label: string;
  subjects: string[];
  startIndex: number;
}

function MultiSelect({
  id,
  label,
  groups,
  values,
  onChange,
  required = false,
  hint,
  error,
  placeholder = "Search and add subjects",
  noResultsText = "No matching subjects.",
}: MultiSelectProps) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [announcement, setAnnouncement] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const listboxId = `${id}-listbox`;

  // Build the visible groups: items that match the search and are not yet selected.
  // Hiding selected items is what prevents duplicate selections.
  const searchText = query.trim().toLowerCase();
  const visibleGroups: VisibleGroup[] = [];
  let optionCount = 0;

  for (const group of groups) {
    const matching = group.subjects.filter(
      (subject) =>
        !values.includes(subject) && subject.toLowerCase().includes(searchText)
    );
    if (matching.length > 0) {
      visibleGroups.push({
        label: group.label,
        subjects: matching,
        startIndex: optionCount,
      });
      optionCount += matching.length;
    }
  }

  const visibleOptions = visibleGroups.flatMap((group) => group.subjects);
  const hasOptions = optionCount > 0;
  const safeActiveIndex = hasOptions ? Math.min(activeIndex, optionCount - 1) : -1;

  const emptyMessage =
    searchText === "" ? "All subjects are already selected." : noResultsText;

  // Scroll the highlighted option into view while navigating with the keyboard.
  useEffect(() => {
    if (!isOpen || safeActiveIndex < 0) {
      return;
    }
    document
      .getElementById(`${id}-option-${safeActiveIndex}`)
      ?.scrollIntoView({ block: "nearest" });
  }, [id, isOpen, safeActiveIndex]);

  function addSubject(subject: string) {
    if (values.includes(subject)) {
      return; // never add the same subject twice
    }
    onChange([...values, subject]);
    setQuery("");
    setActiveIndex(0);
    setAnnouncement(`${subject} added. ${values.length + 1} selected.`);
  }

  function removeSubject(subject: string) {
    onChange(values.filter((value) => value !== subject));
    setAnnouncement(`${subject} removed. ${values.length - 1} selected.`);
    inputRef.current?.focus();
  }

  function handleInputChange(event: ChangeEvent<HTMLInputElement>) {
    setQuery(event.target.value);
    setActiveIndex(0);
    setIsOpen(true);
  }

  function handleBlur() {
    setIsOpen(false);
    setQuery("");
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        if (!isOpen) {
          setActiveIndex(0);
          setIsOpen(true);
        } else if (hasOptions) {
          setActiveIndex((safeActiveIndex + 1) % optionCount);
        }
        break;

      case "ArrowUp":
        event.preventDefault();
        if (!isOpen) {
          setActiveIndex(0);
          setIsOpen(true);
        } else if (hasOptions) {
          setActiveIndex((safeActiveIndex - 1 + optionCount) % optionCount);
        }
        break;

      case "Enter":
        // Never submit the whole form from this field while it is being used.
        if (isOpen || query !== "") {
          event.preventDefault();
        }
        if (isOpen && safeActiveIndex >= 0) {
          addSubject(visibleOptions[safeActiveIndex]);
        }
        break;

      case "Escape":
        if (isOpen) {
          event.preventDefault();
          setIsOpen(false);
          setQuery("");
        }
        break;

      case "Backspace":
        // With an empty text box, Backspace removes the most recent chip.
        if (query === "" && values.length > 0) {
          removeSubject(values[values.length - 1]);
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
        <>
          <div className="combobox">
            <input
              {...control}
              ref={inputRef}
              type="text"
              role="combobox"
              className="form-input combobox-input"
              autoComplete="off"
              placeholder={values.length === 0 ? placeholder : "Add another subject"}
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
              onClick={() => setIsOpen(true)}
              onBlur={handleBlur}
            />

            <div className="combobox-actions">
              <span className="combobox-chevron" aria-hidden="true"></span>
            </div>

            {isOpen && hasOptions && (
              <div
                id={listboxId}
                role="listbox"
                aria-multiselectable="true"
                aria-label={label}
                className="combobox-listbox"
                // Keeps the focus in the text box when an option is clicked.
                onMouseDown={(event) => event.preventDefault()}
              >
                {visibleGroups.map((group, groupIndex) => {
                  const groupLabelId = `${id}-group-${groupIndex}`;

                  return (
                    <div
                      key={group.label}
                      role="group"
                      aria-labelledby={groupLabelId}
                      className="combobox-group"
                    >
                      <div id={groupLabelId} className="combobox-group-label">
                        {group.label}
                      </div>

                      {group.subjects.map((subject, offset) => {
                        const index = group.startIndex + offset;

                        return (
                          <div
                            key={subject}
                            id={`${id}-option-${index}`}
                            role="option"
                            aria-selected={false}
                            className={
                              index === safeActiveIndex
                                ? "combobox-option is-active"
                                : "combobox-option"
                            }
                            onClick={() => addSubject(subject)}
                            onMouseEnter={() => setActiveIndex(index)}
                          >
                            {subject}
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            )}

            {isOpen && !hasOptions && (
              <div className="combobox-listbox">
                <p className="combobox-empty">{emptyMessage}</p>
              </div>
            )}

            {/* Announced by screen readers when the list changes */}
            <div className="visually-hidden" role="status" aria-live="polite">
              {isOpen
                ? hasOptions
                  ? `${optionCount} subjects available. Use the up and down arrow keys to review them.`
                  : emptyMessage
                : ""}
            </div>
          </div>

          {values.length > 0 && (
            <ul className="chip-list" aria-label={`Selected items for ${label}`}>
              {values.map((subject) => (
                <li key={subject} className="chip">
                  <span className="chip-label">{subject}</span>
                  <button
                    type="button"
                    className="chip-remove"
                    aria-label={`Remove ${subject}`}
                    onClick={() => removeSubject(subject)}
                  >
                    &times;
                  </button>
                </li>
              ))}
            </ul>
          )}

          {/* Announces additions and removals to screen readers */}
          <div className="visually-hidden" role="status" aria-live="polite">
            {announcement}
          </div>
        </>
      )}
    </FormField>
  );
}

export default MultiSelect;