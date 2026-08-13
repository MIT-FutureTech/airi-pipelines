import { click, fill } from "@/tour/dom";

export interface TourStep {
  /** `data-tour` value to highlight. Steps without one are centered. */
  anchor?: string;
  title: string;
  body: string;
  side?: "top" | "right" | "bottom" | "left";
  align?: "start" | "center" | "end";
  /** Runs as the step opens, to demonstrate the control it describes. */
  act?: () => void;
}

export const CHAPTER_TWO: TourStep[] = [
  {
    anchor: "risk-list",
    side: "right",
    align: "start",
    title: "Every risk in this paper",
    body:
      "Bold rows like <strong>Harm attributes</strong> are the authors' own grouping. " +
      "Each risk has a marker: <strong>—</strong> to do, <strong>✓</strong> coded, " +
      "<strong>NR</strong> not a risk. The color turns orange when you have unsaved changes. The count on top is your progress in this paper.",
  },
  {
    anchor: "risk-detail",
    side: "left",
    align: "start",
    title: "What you're coding",
    body:
      "Here is the risk as the authors stated it. You can expand their grouping if you want more context. " +
      "If you want to check the original paper, click the <strong>PDF</strong> button in the top-left to download it.",
  },
  {
    anchor: "pipeline-card",
    side: "left",
    align: "center",
    title: "What the pipeline proposed",
    body: "Here is what the pipeline chose, including its reasoning.",
  },
  {
    anchor: "fill-from-pipeline",
    side: "top",
    align: "end",
    title: "Start from the pipeline",
    body:
      "Click this button to copy all four of the pipeline's answers into the controls below (we just pressed it for you). " +
      "Nothing has been written: the app sends your work to Airtable only when you save.",
    act: () => {
      click("fill-from-pipeline");
    },
  },
  {
    anchor: "axis-entity",
    side: "top",
    align: "start",
    title: "Then correct what's wrong",
    body:
      "We changed <strong>Entity</strong> to AI. A solid button is your choice, and a light one is the pipeline's. " +
      "The line underneath now reads <strong>Differs from pipeline</strong>.<br><br>" +
      "You can also toggle <strong>Not a risk</strong> and leave a comment to explain why.",
    act: () => {
      click("axis-entity", "ai");
    },
  },
  {
    anchor: "note-entity",
    side: "top",
    align: "start",
    title: "Say why",
    body: "You can leave a note for each axis. Notes are especially helpful when you disagree with the pipeline.",
    act: () => {
      fill(
        "note-entity",
        "The paper attributes the harm to the system itself.",
      );
    },
  },
  {
    anchor: "save",
    side: "top",
    align: "end",
    title: "Save one risk at a time",
    body:
      "<strong>Save</strong> writes this risk's classifications to Airtable (<strong>⌘/Ctrl+Enter</strong> does the same). " +
      "Greyed out means there's nothing to save; light means you can save but axes are still missing; " +
      "solid means the risk is complete.<br><br>" +
      "Move between risks with <strong>←</strong> and <strong>→</strong> or clicking in the sidebar.",
  },
  {
    title: "That's the loop",
    body:
      "Read the risk, check the pipeline's answer, correct it and say why, save. " +
      "Nothing you just did was saved: this was a frozen demo paper, and it resets every time. " +
      "Next stop, your own papers.",
  },
];
