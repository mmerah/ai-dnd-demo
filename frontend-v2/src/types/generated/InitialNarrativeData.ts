/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Timestamp = string;
export type ScenarioTitle = string;
export type Narrative = string;

/**
 * Data for initial narrative event.
 */
export interface InitialNarrativeData {
  timestamp?: Timestamp;
  scenario_title: ScenarioTitle;
  narrative: Narrative;
}
