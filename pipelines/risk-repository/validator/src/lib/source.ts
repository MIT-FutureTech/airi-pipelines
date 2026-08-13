import type {
  RiskManifestResponse,
  SaveCodingsRequest,
  SaveCodingsResponse,
} from "@shared/classification";
import {
  fetchRiskManifest,
  getRiskManifest,
  type RiskManifestParams,
  saveCodings,
} from "@/lib/api";

export interface ClassificationSource {
  load: () => Promise<RiskManifestResponse>;
  refresh: () => Promise<RiskManifestResponse>;
  save: (body: SaveCodingsRequest) => Promise<SaveCodingsResponse>;
}

export function airtableSource(
  params: RiskManifestParams,
): ClassificationSource {
  return {
    load: () => getRiskManifest(params),
    refresh: () => fetchRiskManifest(params),
    save: (body) => saveCodings(body),
  };
}
