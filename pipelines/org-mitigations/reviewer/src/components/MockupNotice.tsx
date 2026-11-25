import { Alert, List, Text } from "@mantine/core";
import type { RunSettings } from "@/lib/types";

interface MockupNoticeProps {
  run: RunSettings;
  companyCount: number;
  codeCount: number;
}

export function MockupNotice({
  run,
  companyCount,
  codeCount,
}: MockupNoticeProps) {
  return (
    <Alert color="blue" title="A mock-up for feedback">
      <Text>
        Click a shaded cell to see the quotes behind it. Then record whether the
        company discloses that kind of mitigation.
      </Text>
      <List mt="xs">
        <List.Item>
          Nothing is saved. Your choices disappear when you reload the page.
        </List.Item>
        <List.Item>
          {`The quotes were found by an LLM (${run.model}) and haven't been reviewed. There are likely false positives and false negatives.`}
        </List.Item>
        <List.Item>
          {`It covers ${companyCount} companies and the ${codeCount} mitigation domain codes. The instrument taxonomy isn't included.`}
        </List.Item>
      </List>
    </Alert>
  );
}
