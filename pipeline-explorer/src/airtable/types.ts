export type AccessMode = "read" | "write" | "read-write";

/** How a specific repo interacts with an Airtable field */
export interface FieldAccess {
  mode: AccessMode;
  /** Airtable formula used when reading, e.g. `{screening_status}='screened'` */
  filterFormula?: string;
  /** Human-readable description of what gets written, e.g. `"Validated"` */
  writtenAs?: string;
  /** Free-form context for the popover */
  notes?: string;
}

/** A single field inside an Airtable table */
export interface AirtableField {
  name: string;
  type: string;
  /** Keyed by repo short name, e.g. "greylitsearcher" */
  access: Record<string, FieldAccess>;
}

/** An Airtable table and its field-level access map */
export interface AirtableTable {
  tableId: string;
  name: string;
  description?: string;
  fields: AirtableField[];
}

/** An Airtable base with all its tables */
export interface AirtableBase {
  baseId: string;
  name: string;
  tables: AirtableTable[];
}
