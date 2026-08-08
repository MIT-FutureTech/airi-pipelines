import { Alert, Button, Center, Stack } from "@mantine/core";
import type { FallbackProps } from "react-error-boundary";

export function ErrorScreen({ error }: FallbackProps) {
  return (
    <Center h="100vh" p="md">
      <Stack gap="md" maw={600}>
        <Alert color="red" title="Error">
          {error instanceof Error ? error.message : String(error)}
        </Alert>
        <Button
          variant="default"
          onClick={() => window.location.assign("/")}
          style={{ alignSelf: "flex-start" }}
        >
          Back to tasks
        </Button>
      </Stack>
    </Center>
  );
}
