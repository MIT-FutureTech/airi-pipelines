import { Alert, List, Text } from "@mantine/core";

interface MockupNoticeProps {
  companyCount: number;
}

export function MockupNotice({ companyCount }: MockupNoticeProps) {
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
          The quotes were found by an LLM and haven't been reviewed. There are
          likely false positives and false negatives.
        </List.Item>
        <List.Item>
          {`It covers the ${companyCount} companies where the LLM found at least one mitigation.`}
        </List.Item>
      </List>
    </Alert>
  );
}
