import { AirtableView } from "@/airtable/components/AirtableView";
import { airtableBases } from "@/airtable/data";

export default function AirtablePage() {
  return <AirtableView bases={airtableBases} />;
}
