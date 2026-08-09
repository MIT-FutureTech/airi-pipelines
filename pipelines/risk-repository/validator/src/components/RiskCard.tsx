import {
  Accordion,
  Anchor,
  Badge,
  Button,
  Group,
  Paper,
  ScrollArea,
  Select,
  Stack,
  Switch,
  Text,
} from "@mantine/core";
import {
  AXIS_FIELDS,
  type EvidenceItem,
  NOT_A_RISK,
  REVIEW_FIELDS,
  type ReviewField,
  type RiskEntry,
} from "@shared/classification";
import { isCoded } from "@shared/coding";
import { useMemo } from "react";
import { type Draft, draftCodings, withNotARisk } from "@/lib/draft";
import { SUBDOMAIN_GROUPS, SUBDOMAIN_LABELS } from "@/lib/subdomains";

interface AxisOption {
  value: string;
  label: string;
}

const CAUSAL_AXES: {
  field: ReviewField;
  label: string;
  options: AxisOption[];
}[] = [
  {
    field: "entity",
    label: "Entity",
    options: [
      { value: "human", label: "Human" },
      { value: "ai", label: "AI" },
      { value: "other", label: "Other" },
    ],
  },
  {
    field: "intent",
    label: "Intent",
    options: [
      { value: "intentional", label: "Intentional" },
      { value: "unintentional", label: "Unintentional" },
      { value: "other", label: "Other" },
    ],
  },
  {
    field: "timing",
    label: "Timing",
    options: [
      { value: "pre-deployment", label: "Pre-deployment" },
      { value: "post-deployment", label: "Post-deployment" },
      { value: "other", label: "Other" },
    ],
  },
];

interface Props {
  entry: RiskEntry;
  ancestors: RiskEntry[];
  expandedAncestors: string[];
  draft: Draft;
  dirty: boolean;
  saving: boolean;
  saved: boolean;
  error: string | null;
  position: number;
  total: number;
  onDraftChange: (draft: Draft) => void;
  onSave: () => void;
  onExpandedAncestorsChange: (ids: string[]) => void;
}

export function RiskCard({
  entry,
  ancestors,
  expandedAncestors,
  draft,
  dirty,
  saving,
  saved,
  error,
  position,
  total,
  onDraftChange,
  onSave,
  onExpandedAncestorsChange,
}: Props) {
  const notARisk = draft.validity === NOT_A_RISK;
  const coded = isCoded(draftCodings(draft));

  const suggestions = useMemo(() => {
    const map = {} as Record<ReviewField, string | null>;
    for (const field of REVIEW_FIELDS) {
      map[field] = null;
    }
    for (const response of entry.pipelineResponses) {
      map[response.field] = response.value;
    }
    return map;
  }, [entry.pipelineResponses]);

  const hasSuggestions = AXIS_FIELDS.some(
    (field) => suggestions[field] !== null,
  );

  const setValue = (field: ReviewField, value: string) => {
    onDraftChange({ ...draft, [field]: value });
  };

  const acceptSuggestions = () => {
    const next: Draft = { ...draft, validity: null };
    for (const field of AXIS_FIELDS) {
      const suggested = suggestions[field];
      if (suggested !== null) {
        next[field] = suggested;
      }
    }
    onDraftChange(next);
  };

  return (
    <Stack gap="md" h="100%">
      <Group justify="space-between" align="center">
        <Text size="sm" c="dimmed">
          {position} / {total} · {entry.readableId}
        </Text>
        {notARisk ? (
          <Badge color="gray" variant="light">
            not a risk
          </Badge>
        ) : coded ? (
          <Badge color="green" variant="light">
            coded
          </Badge>
        ) : null}
      </Group>

      <ScrollArea style={{ flex: 1, minHeight: 0 }}>
        <Stack gap="md">
          {ancestors.length > 0 ? (
            <AncestorTrail
              ancestors={ancestors}
              expanded={expandedAncestors}
              onExpandedChange={onExpandedAncestorsChange}
            />
          ) : null}
          <Text fw={600} size="lg">
            {entry.name}
          </Text>
          <RiskDetails risk={entry} />
        </Stack>
      </ScrollArea>

      <Stack gap="sm">
        {hasSuggestions ? (
          <Group justify="space-between">
            <Text size="xs" c="dimmed">
              Pipeline classification shown below.
            </Text>
            <Button
              size="xs"
              variant="light"
              onClick={acceptSuggestions}
              disabled={notARisk}
            >
              Accept suggestions
            </Button>
          </Group>
        ) : null}
        <Switch
          label="Not a risk"
          checked={notARisk}
          onChange={(event) => {
            onDraftChange(withNotARisk(draft, event.currentTarget.checked));
          }}
        />
        {CAUSAL_AXES.map((axis) => (
          <AxisButtons
            key={axis.field}
            label={axis.label}
            options={axis.options}
            value={draft[axis.field]}
            suggested={suggestions[axis.field]}
            disabled={notARisk}
            onSelect={(value) => {
              setValue(axis.field, value);
            }}
          />
        ))}
        <Stack gap={4}>
          <Text size="sm" fw={500}>
            Subdomain
          </Text>
          <Select
            placeholder="Select subdomain"
            data={SUBDOMAIN_GROUPS.map((group) => ({
              group: group.domain,
              items: group.items,
            }))}
            value={draft.subdomain}
            onChange={(value) => {
              if (value !== null) {
                setValue("subdomain", value);
              }
            }}
            disabled={notARisk}
            searchable
          />
          {suggestions.subdomain !== null &&
          draft.subdomain === null &&
          !notARisk ? (
            <Group gap="xs">
              <Text size="xs" c="dimmed">
                Pipeline:{" "}
                {SUBDOMAIN_LABELS[suggestions.subdomain] ??
                  suggestions.subdomain}
              </Text>
              <Anchor
                component="button"
                type="button"
                size="xs"
                onClick={() => {
                  const suggested = suggestions.subdomain;
                  if (suggested !== null) {
                    setValue("subdomain", suggested);
                  }
                }}
              >
                Use
              </Anchor>
            </Group>
          ) : null}
        </Stack>
        <Group justify="space-between" align="center">
          <SaveStatus
            dirty={dirty}
            saving={saving}
            saved={saved}
            error={error}
          />
          <Button onClick={onSave} disabled={!dirty} loading={saving}>
            Save
          </Button>
        </Group>
      </Stack>
    </Stack>
  );
}

interface SaveStatusProps {
  dirty: boolean;
  saving: boolean;
  saved: boolean;
  error: string | null;
}

function SaveStatus({ dirty, saving, saved, error }: SaveStatusProps) {
  if (error !== null) {
    return (
      <Text size="sm" c="red">
        {error}
      </Text>
    );
  }
  if (saving) {
    return (
      <Text size="sm" c="dimmed">
        Saving…
      </Text>
    );
  }
  if (dirty) {
    return (
      <Text size="sm" c="dimmed">
        Unsaved changes
      </Text>
    );
  }
  if (saved) {
    return (
      <Text size="sm" c="green">
        Saved
      </Text>
    );
  }
  return null;
}

interface AncestorTrailProps {
  ancestors: RiskEntry[];
  expanded: string[];
  onExpandedChange: (ids: string[]) => void;
}

function AncestorTrail({
  ancestors,
  expanded,
  onExpandedChange,
}: AncestorTrailProps) {
  return (
    <Stack gap={4}>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
        Authors' grouping
      </Text>
      <Accordion
        variant="contained"
        chevronPosition="left"
        multiple
        value={expanded}
        onChange={onExpandedChange}
      >
        {ancestors.map((ancestor) => (
          <Accordion.Item key={ancestor.id} value={ancestor.id}>
            <Accordion.Control>
              <Stack gap={0}>
                <Text size="sm" fw={500}>
                  {ancestor.name}
                </Text>
                <Text size="xs" c="dimmed">
                  {ancestor.readableId}
                </Text>
              </Stack>
            </Accordion.Control>
            <Accordion.Panel>
              <RiskDetails risk={ancestor} />
            </Accordion.Panel>
          </Accordion.Item>
        ))}
      </Accordion>
    </Stack>
  );
}

function RiskDetails({ risk }: { risk: RiskEntry }) {
  const showQuote =
    risk.supportingQuote !== "" && risk.supportingQuote !== risk.description;
  const empty =
    risk.description === "" &&
    !showQuote &&
    risk.additionalEvidence.length === 0;

  if (empty) {
    return (
      <Text size="sm" c="dimmed">
        No description or evidence recorded.
      </Text>
    );
  }

  return (
    <Stack gap="md">
      {risk.description !== "" ? (
        <RiskField
          label={
            risk.descriptionPage === null
              ? "Description"
              : `Description (p. ${risk.descriptionPage})`
          }
        >
          <Text style={{ whiteSpace: "pre-wrap" }}>{risk.description}</Text>
        </RiskField>
      ) : null}
      {showQuote ? (
        <RiskField label="Supporting quote">
          <Quote>{risk.supportingQuote}</Quote>
        </RiskField>
      ) : null}
      {risk.additionalEvidence.length > 0 ? (
        <RiskField label="Additional evidence">
          <Stack gap="xs">
            {risk.additionalEvidence.map((item) => (
              <EvidenceCard key={item.index} item={item} />
            ))}
          </Stack>
        </RiskField>
      ) : null}
    </Stack>
  );
}

function Quote({ children }: { children: string }) {
  return (
    <Text
      fs="italic"
      style={{
        whiteSpace: "pre-wrap",
        borderInlineStart: "2px solid var(--mantine-color-default-border)",
        paddingInlineStart: "var(--mantine-spacing-sm)",
      }}
    >
      {children}
    </Text>
  );
}

function EvidenceCard({ item }: { item: EvidenceItem }) {
  return (
    <Paper withBorder p="xs">
      <Stack gap={4}>
        {item.fields.map((field) => (
          <Group key={field.key} gap="xs" align="flex-start" wrap="nowrap">
            <Text size="xs" c="dimmed" tt="uppercase" fw={600} miw="4.5rem">
              {field.key}
            </Text>
            <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
              {field.value}
            </Text>
          </Group>
        ))}
      </Stack>
    </Paper>
  );
}

interface AxisButtonsProps {
  label: string;
  options: AxisOption[];
  value: string | null;
  suggested: string | null;
  disabled: boolean;
  onSelect: (value: string) => void;
}

function AxisButtons({
  label,
  options,
  value,
  suggested,
  disabled,
  onSelect,
}: AxisButtonsProps) {
  const suggestedLabel =
    suggested === null
      ? null
      : (options.find((option) => option.value === suggested)?.label ??
        suggested);
  return (
    <Stack gap={4}>
      <Text size="sm" fw={500}>
        {label}
      </Text>
      <Group gap="xs">
        {options.map((option) => (
          <Button
            key={option.value}
            size="xs"
            variant={
              value === option.value
                ? "filled"
                : option.value === suggested
                  ? "outline"
                  : "light"
            }
            onClick={() => {
              onSelect(option.value);
            }}
            disabled={disabled}
          >
            {option.label}
          </Button>
        ))}
      </Group>
      {suggestedLabel !== null && value === null && !disabled ? (
        <Text size="xs" c="dimmed">
          Pipeline: {suggestedLabel}
        </Text>
      ) : null}
    </Stack>
  );
}

interface RiskFieldProps {
  label: string;
  children: React.ReactNode;
}

function RiskField({ label, children }: RiskFieldProps) {
  return (
    <Stack gap={2}>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
        {label}
      </Text>
      {children}
    </Stack>
  );
}
