import type {
  EvidenceItem,
  ReviewField,
  ReviewMode,
  ReviewResponse,
  RiskEntry,
} from "@api/_classification";
import {
  Alert,
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
import { useMemo, useRef, useState } from "react";
import { deleteReview, submitReview } from "@/lib/api";
import {
  AXIS_FIELDS,
  NOT_A_RISK,
  REJECTED_ORIGIN,
  REVIEW_FIELDS,
} from "@/lib/fields";
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
  mode: ReviewMode;
  position: number;
  total: number;
  onResponsesChanged: (riskId: string, responses: ReviewResponse[]) => void;
}

export function RiskCard({
  reviewer,
  entry,
  ancestors,
  mode,
  position,
  total,
  onResponsesChanged,
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
          {entry.codable ? `${position} / ${total} · ` : ""}
          {entry.readableId}
        </Text>
        <Group gap="xs">
          {entry.origin === REJECTED_ORIGIN ? (
            <Badge color="red" variant="light">
              rejected in extraction
            </Badge>
          ) : null}
          {!entry.codable ? (
            <Badge color="gray" variant="light">
              context only
            </Badge>
          ) : notARisk ? (
            <Badge color="gray" variant="light">
              not a risk
            </Badge>
          ) : coded ? (
            <Badge color="green" variant="light">
              coded
            </Badge>
          ) : null}
        </Group>
      </Group>

      <ScrollArea style={{ flex: 1, minHeight: 0 }}>
        <Stack gap="md">
          {ancestors.length > 0 ? (
            <AncestorTrail ancestors={ancestors} />
          ) : null}
          <Text fw={600} size="lg">
            {entry.name}
          </Text>
          {entry.description !== "" ? (
            <RiskField
              label={
                entry.descriptionPage === null
                  ? "Description"
                  : `Description (p. ${entry.descriptionPage})`
              }
            >
              <Text style={{ whiteSpace: "pre-wrap" }}>
                {entry.description}
              </Text>
            </RiskField>
          ) : null}
          {entry.supportingQuote !== "" ? (
            <RiskField label="Supporting quote">
              <Text style={{ whiteSpace: "pre-wrap" }} fs="italic">
                {entry.supportingQuote}
              </Text>
            </RiskField>
          ) : null}
          {entry.additionalEvidence.length > 0 ? (
            <RiskField label="Additional evidence">
              <Stack gap="xs">
                {entry.additionalEvidence.map((item) => (
                  <EvidenceCard key={item.index} item={item} />
                ))}
              </Stack>
            </RiskField>
          ) : null}
        </Stack>
      </ScrollArea>

      {entry.codable ? (
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
      ) : (
        <Alert color="gray" variant="light">
          Only the deepest risks are classified. This entry groups the risks
          below it and is shown for context.
        </Alert>
      )}
    </Stack>
  );
}

function AncestorTrail({ ancestors }: { ancestors: RiskEntry[] }) {
  return (
    <Paper withBorder p="sm" bg="var(--mantine-color-default-hover)">
      <Stack gap="xs">
        <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
          Authors' grouping
        </Text>
        {ancestors.map((ancestor, index) => (
          <Stack key={ancestor.id} gap={2} pl={index * 12}>
            <Text size="sm" fw={500}>
              {ancestor.name}
            </Text>
            {ancestor.description !== "" ? (
              <Text size="xs" c="dimmed">
                {ancestor.description}
              </Text>
            ) : null}
            {ancestor.supportingQuote !== "" &&
            ancestor.supportingQuote !== ancestor.description ? (
              <Text size="xs" c="dimmed" fs="italic">
                {ancestor.supportingQuote}
              </Text>
            ) : null}
          </Stack>
        ))}
      </Stack>
    </Paper>
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
