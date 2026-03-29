import type { AirtableBase } from "@/airtable/types";
import { classifications } from "./classifications";

export const incidentTracker: AirtableBase = {
  baseId: "appYXeL8YwZfAy4kF",
  name: "Incident Tracker Live",
  tables: [classifications],
};
