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
  type ReviewMode,
  type ReviewResponse,
  type RiskEntry,
} from "@shared/classification";
import { useMemo, useRef, useState } from "react";
import { deleteReview, submitReview } from "@/lib/api";
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

interface FieldState {
  value: string | null;
  reviewId: string | null;
  saving: boolean;
  error: string | null;
}

type FieldStates = Record<ReviewField, FieldState>;

const EMPTY_FIELD: FieldState = {
  value: null,
  reviewId: null,
  saving: false,
  error: null,
};

function initFieldStates(entry: RiskEntry): FieldStates {
  const states = {} as FieldStates;
  for (const field of REVIEW_FIELDS) {
    states[field] = { ...EMPTY_FIELD };
  }
  for (const response of entry.responses) {
    states[response.field] = {
      value: response.value,
      reviewId: response.id,
      saving: false,
      error: null,
    };
  }
  return states;
}

interface Props {
  reviewer: string;
  entry: RiskEntry;
  ancestors: RiskEntry[];
  expandedAncestors: string[];
  mode: ReviewMode;
  position: number;
  total: number;
  onResponsesChanged: (riskId: string, responses: ReviewResponse[]) => void;
  onExpandedAncestorsChange: (ids: string[]) => void;
}

export function RiskCard({
  reviewer,
  entry,
  ancestors,
  expandedAncestors,
  mode,
  position,
  total,
  onResponsesChanged,
  onExpandedAncestorsChange,
}: Props) {
  const [fields, setFields] = useState<FieldStates>(() =>
    initFieldStates(entry),
  );
  const fieldsRef = useRef(fields);
  fieldsRef.current = fields;

  const notARisk = fields.validity.value === NOT_A_RISK;
  const coded =
    notARisk || AXIS_FIELDS.every((field) => fields[field].value !== null);

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

  const toResponses = (states: FieldStates): ReviewResponse[] => {
    const responses: ReviewResponse[] = [];
    for (const field of REVIEW_FIELDS) {
      const state = states[field];
      if (state.value !== null && state.reviewId !== null) {
        responses.push({
          id: state.reviewId,
          field,
          value: state.value,
          mode,
          comment: null,
        });
      }
    }
    return responses;
  };

  const saveField = async (field: ReviewField, value: string) => {
    setFields((prev) => ({
      ...prev,
      [field]: { ...prev[field], value, saving: true, error: null },
    }));
    try {
      const response = await submitReview({
        reviewer,
        riskId: entry.id,
        reviewId: fieldsRef.current[field].reviewId,
        field,
        value,
        mode,
        comment: null,
      });
      const next: FieldStates = {
        ...fieldsRef.current,
        [field]: {
          value,
          reviewId: response.reviewId,
          saving: false,
          error: null,
        },
      };
      if (field === "validity" && value === NOT_A_RISK) {
        for (const axis of AXIS_FIELDS) {
          next[axis] = { ...EMPTY_FIELD };
        }
      }
      setFields(next);
      onResponsesChanged(entry.id, toResponses(next));
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setFields((prev) => ({
        ...prev,
        [field]: { ...prev[field], saving: false, error: message },
      }));
    }
  };

  const clearValidity = async () => {
    const reviewId = fieldsRef.current.validity.reviewId;
    if (reviewId === null) {
      return;
    }
    setFields((prev) => ({
      ...prev,
      validity: { ...prev.validity, saving: true, error: null },
    }));
    try {
      await deleteReview(reviewId);
      const next: FieldStates = {
        ...fieldsRef.current,
        validity: { ...EMPTY_FIELD },
      };
      setFields(next);
      onResponsesChanged(entry.id, toResponses(next));
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setFields((prev) => ({
        ...prev,
        validity: { ...prev.validity, saving: false, error: message },
      }));
    }
  };

  const acceptSuggestions = async () => {
    for (const field of AXIS_FIELDS) {
      const suggested = suggestions[field];
      if (suggested !== null && fields[field].value === null) {
        await saveField(field, suggested);
      }
    }
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
            if (event.currentTarget.checked) {
              saveField("validity", NOT_A_RISK);
            } else {
              clearValidity();
            }
          }}
          disabled={fields.validity.saving}
        />
        {fields.validity.error !== null ? (
          <Text c="red" size="xs">
            {fields.validity.error}
          </Text>
        ) : null}
        {CAUSAL_AXES.map((axis) => (
          <AxisButtons
            key={axis.field}
            label={axis.label}
            options={axis.options}
            state={fields[axis.field]}
            suggested={suggestions[axis.field]}
            disabled={notARisk}
            onSelect={(value) => saveField(axis.field, value)}
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
            value={fields.subdomain.value}
            onChange={(value) => {
              if (value !== null) {
                saveField("subdomain", value);
              }
            }}
            disabled={notARisk || fields.subdomain.saving}
            searchable
          />
          {suggestions.subdomain !== null &&
          fields.subdomain.value === null &&
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
                    saveField("subdomain", suggested);
                  }
                }}
              >
                Use
              </Anchor>
            </Group>
          ) : null}
          {fields.subdomain.error !== null ? (
            <Text c="red" size="xs">
              {fields.subdomain.error}
            </Text>
          ) : null}
        </Stack>
      </Stack>
    </Stack>
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
  state: FieldState;
  suggested: string | null;
  disabled: boolean;
  onSelect: (value: string) => void;
}

function AxisButtons({
  label,
  options,
  state,
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
              state.value === option.value
                ? "filled"
                : option.value === suggested
                  ? "outline"
                  : "light"
            }
            onClick={() => onSelect(option.value)}
            disabled={disabled || state.saving}
          >
            {option.label}
          </Button>
        ))}
      </Group>
      {suggestedLabel !== null && state.value === null && !disabled ? (
        <Text size="xs" c="dimmed">
          Pipeline: {suggestedLabel}
        </Text>
      ) : null}
      {state.error !== null ? (
        <Text c="red" size="xs">
          {state.error}
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
