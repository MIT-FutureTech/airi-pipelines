import {
  Accordion,
  Anchor,
  Badge,
  Button,
  Group,
  Paper,
  ScrollArea,
  Select,
  SimpleGrid,
  Stack,
  Switch,
  Text,
  Textarea,
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
import { type ReactNode, useMemo } from "react";
import { PipelineCard } from "@/components/PipelineCard";
import {
  type Draft,
  draftCodings,
  withComment,
  withNotARisk,
  withValue,
} from "@/lib/draft";
import { type AxisOption, CAUSAL_AXES, valueLabel } from "@/lib/fields";
import { SUBDOMAIN_GROUPS } from "@/lib/subdomains";

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
  const notARisk = draft.validity.value === NOT_A_RISK;
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
  const suggestedSubdomain = suggestions.subdomain;

  const setValue = (field: ReviewField, value: string) => {
    onDraftChange(withValue(draft, field, value));
  };

  const setComment = (field: ReviewField, comment: string) => {
    onDraftChange(withComment(draft, field, comment));
  };

  const fillFromPipeline = () => {
    let next = withNotARisk(draft, false);
    for (const field of AXIS_FIELDS) {
      const suggested = suggestions[field];
      if (suggested !== null) {
        next = withValue(next, field, suggested);
      }
    }
    onDraftChange(next);
  };

  const remaining = notARisk
    ? 0
    : AXIS_FIELDS.filter((field) => draft[field].value === null).length;

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
          {hasSuggestions ? (
            <PipelineCard responses={entry.pipelineResponses} />
          ) : null}
        </Stack>
      </ScrollArea>

      <Stack gap="sm">
        {hasSuggestions ? (
          <Group justify="end">
            <Button
              variant="light"
              onClick={fillFromPipeline}
              disabled={notARisk}
            >
              Fill from pipeline
            </Button>
          </Group>
        ) : null}
        <FieldRow
          control={
            <Switch
              label="Not a risk"
              checked={notARisk}
              onChange={(event) => {
                onDraftChange(withNotARisk(draft, event.currentTarget.checked));
              }}
            />
          }
          comment={
            <NoteField
              value={draft.validity.comment}
              disabled={!notARisk}
              placeholder={
                notARisk
                  ? "Why is this not a risk?"
                  : "Mark not a risk to add a note"
              }
              onChange={(comment) => {
                setComment("validity", comment);
              }}
            />
          }
        />
        {CAUSAL_AXES.map((axis) => (
          <FieldRow
            key={axis.field}
            control={
              <AxisButtons
                label={axis.label}
                options={axis.options}
                value={draft[axis.field].value}
                suggested={suggestions[axis.field]}
                disabled={notARisk}
                onSelect={(value) => {
                  setValue(axis.field, value);
                }}
              />
            }
            comment={
              <NoteField
                value={draft[axis.field].comment}
                disabled={notARisk || draft[axis.field].value === null}
                placeholder={notePlaceholder(
                  axis.label,
                  draft[axis.field].value,
                )}
                onChange={(comment) => {
                  setComment(axis.field, comment);
                }}
              />
            }
          />
        ))}
        <FieldRow
          control={
            <Stack gap={4}>
              <Text size="sm" fw={500}>
                Subdomain
              </Text>
              <Select
                placeholder={
                  suggestedSubdomain
                    ? valueLabel("subdomain", suggestedSubdomain)
                    : "Select subdomain"
                }
                data={SUBDOMAIN_GROUPS.map((group) => ({
                  group: group.domain,
                  items: group.items,
                }))}
                value={draft.subdomain.value}
                onChange={(value) => {
                  if (value !== null) {
                    setValue("subdomain", value);
                  }
                }}
                disabled={notARisk}
                searchable
              />
              {suggestedSubdomain !== null && !notARisk ? (
                <Group gap="xs">
                  <Text size="xs" c="dimmed">
                    {pipelineHint(
                      draft.subdomain.value,
                      suggestedSubdomain,
                      valueLabel("subdomain", suggestedSubdomain),
                    )}
                  </Text>
                  {draft.subdomain.value === suggestedSubdomain ? null : (
                    <Anchor
                      component="button"
                      type="button"
                      size="xs"
                      onClick={() => {
                        setValue("subdomain", suggestedSubdomain);
                      }}
                    >
                      Use
                    </Anchor>
                  )}
                </Group>
              ) : null}
            </Stack>
          }
          comment={
            <NoteField
              value={draft.subdomain.comment}
              disabled={notARisk || draft.subdomain.value === null}
              placeholder={notePlaceholder("Subdomain", draft.subdomain.value)}
              onChange={(comment) => {
                setComment("subdomain", comment);
              }}
            />
          }
        />
        <Group justify="space-between" align="center">
          <SaveStatus
            dirty={dirty}
            saving={saving}
            saved={saved}
            error={error}
            remaining={remaining}
          />
          <Button
            onClick={onSave}
            variant={remaining ? "light" : "filled"}
            disabled={!dirty}
            loading={saving}
          >
            Save
          </Button>
        </Group>
      </Stack>
    </Stack>
  );
}

function pipelineHint(
  value: string | null,
  suggested: string,
  suggestedLabel: string,
): string {
  if (value === null) {
    return `Pipeline: ${suggestedLabel}`;
  }
  return value === suggested
    ? "Matches pipeline"
    : `Differs from pipeline: ${suggestedLabel}`;
}

interface FieldRowProps {
  control: ReactNode;
  comment: ReactNode;
}

function FieldRow({ control, comment }: FieldRowProps) {
  return (
    <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md" verticalSpacing="xs">
      {control}
      {comment}
    </SimpleGrid>
  );
}

interface NoteFieldProps {
  value: string;
  placeholder: string;
  disabled: boolean;
  onChange: (comment: string) => void;
}

function NoteField({ value, placeholder, disabled, onChange }: NoteFieldProps) {
  return (
    <Textarea
      value={value}
      placeholder={placeholder}
      disabled={disabled}
      onChange={(event) => {
        onChange(event.currentTarget.value);
      }}
      autosize
      minRows={2}
      maxRows={6}
    />
  );
}

function notePlaceholder(label: string, value: string | null): string {
  return value === null
    ? "Select a value first"
    : `Note on ${label.toLowerCase()}`;
}

interface SaveStatusProps {
  dirty: boolean;
  saving: boolean;
  saved: boolean;
  error: string | null;
  remaining: number;
}

function SaveStatus({
  dirty,
  saving,
  saved,
  error,
  remaining,
}: SaveStatusProps) {
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
  const outstanding =
    remaining === 0
      ? null
      : `${remaining} ${remaining === 1 ? "axis" : "axes"} left`;
  if (dirty) {
    return (
      <Text size="sm" c="dimmed">
        {outstanding === null
          ? "Unsaved changes"
          : `Unsaved changes · ${outstanding}`}
      </Text>
    );
  }
  if (saved) {
    return (
      <Text size="sm" c="green">
        {outstanding === null ? "Saved" : `Saved · ${outstanding}`}
      </Text>
    );
  }
  return outstanding === null ? null : (
    <Text size="sm" c="dimmed">
      {outstanding}
    </Text>
  );
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
      {suggested !== null && suggestedLabel !== null && !disabled ? (
        <Text size="xs" c="dimmed">
          {pipelineHint(value, suggested, suggestedLabel)}
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
