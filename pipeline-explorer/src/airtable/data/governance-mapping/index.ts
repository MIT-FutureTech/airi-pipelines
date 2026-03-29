import type { AirtableBase } from "@/airtable/types";
import { uniqueUpload } from "./unique-upload";

export const governanceMapping: AirtableBase = {
  baseId: "appLSe43cSlDiYZyA",
  name: "AI Risk Governance Mapping",
  tables: [uniqueUpload],
};
