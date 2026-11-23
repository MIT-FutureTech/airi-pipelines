import type { Judgement } from "@shared/judgements";
import { useRef, useState } from "react";
import { saveJudgement } from "@/lib/api";
import { cellKey } from "@/lib/cells";
import { judgementsByCell, saveRequest } from "@/lib/judgements";
import { createSaveQueue, type SaveStatus } from "@/lib/saving";

const enqueueSave = createSaveQueue(saveJudgement);

export function useJudgements(saved: Judgement[]) {
  const [judgements, setJudgements] = useState(() => judgementsByCell(saved));
  const [saveStatuses, setSaveStatuses] = useState(
    () => new Map<string, SaveStatus>(),
  );
  const saveVersions = useRef(new Map<string, number>());

  const setSaveStatus = (key: string, status: SaveStatus) => {
    setSaveStatuses((current) => new Map(current).set(key, status));
  };

  const change = (judgement: Judgement) => {
    const key = cellKey(judgement.companyId, judgement.codeRecordId);
    setJudgements((current) => new Map(current).set(key, judgement));
  };

  const save = (judgement: Judgement, companyName: string, codeKey: string) => {
    change(judgement);
    const key = cellKey(judgement.companyId, judgement.codeRecordId);
    const version = (saveVersions.current.get(key) ?? 0) + 1;
    saveVersions.current.set(key, version);
    const isLatest = () => saveVersions.current.get(key) === version;
    setSaveStatus(key, "saving");
    enqueueSave(key, saveRequest(judgement, companyName, codeKey)).then(
      () => {
        if (isLatest()) {
          setSaveStatus(key, "saved");
        }
      },
      () => {
        if (isLatest()) {
          setSaveStatus(key, "failed");
        }
      },
    );
  };

  return { judgements, saveStatuses, change, save };
}
