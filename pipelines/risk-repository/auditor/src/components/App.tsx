import { AppShell, Burger, Group, Text } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";

export function App() {
  const [opened, { toggle }] = useDisclosure();

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{
        width: 320,
        breakpoint: "sm",
        collapsed: { mobile: !opened },
      }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
          <Text fw={600}>Risk Repository Auditor</Text>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="md">
        <Text c="dimmed" size="sm">
          Document list will go here
        </Text>
      </AppShell.Navbar>
      <AppShell.Main>
        <Text c="dimmed">Document detail will go here</Text>
      </AppShell.Main>
    </AppShell>
  );
}
