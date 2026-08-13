import {
  REVIEW_FIELDS,
  type ReviewResponse,
  type RiskManifestResponse,
  type SaveCodingsRequest,
  type SaveCodingsResponse,
} from "@shared/classification";
import type { ClassificationSource } from "@/lib/source";
import { DEMO_PAPER } from "@/tour/demoPaper";

export function demoSource(): ClassificationSource {
  const manifest: RiskManifestResponse = structuredClone(DEMO_PAPER);

  const save = (body: SaveCodingsRequest): SaveCodingsResponse => {
    const risk = manifest.risks.find((entry) => entry.id === body.riskId);
    if (risk === undefined) {
      throw new Error(`Unknown risk in the demo paper: ${body.riskId}`);
    }
    const responses: ReviewResponse[] = body.codings.map((coding) => ({
      id: `demo:${body.riskId}:${coding.field}`,
      field: coding.field,
      value: coding.value,
      mode: body.mode,
      comment: coding.comment,
    }));
    responses.sort(
      (a, b) => REVIEW_FIELDS.indexOf(a.field) - REVIEW_FIELDS.indexOf(b.field),
    );
    risk.responses = responses;
    return { riskId: body.riskId, responses };
  };

  return {
    load: () => Promise.resolve(manifest),
    refresh: () => Promise.resolve(manifest),
    save: (body) => Promise.resolve(save(body)),
  };
}
