import type {
  ReviewField,
  ReviewMode,
  ReviewResponse,
  RiskEntry,
} from "@api/_classification";
import {
  Anchor,
  Badge,
  Button,
  Group,
  ScrollArea,
  Select,
  Stack,
  Switch,
  Text,
} from "@mantine/core";
import { useMemo, useRef, useState } from "react";
import { submitReview } from "@/lib/api";
import { AXIS_FIELDS, REVIEW_FIELDS } from "@/lib/fields";
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
  mode: ReviewMode;
  position: number;
  total: number;
  onResponsesChanged: (riskId: string, responses: ReviewResponse[]) => void;
}

export function RiskCard({
  reviewer,
  entry,
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

  const notARisk = fields.validity.value === "not-a-risk";
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
      if (field === "validity" && value === "not-a-risk") {
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
          <RiskField label="Description">
            <Text style={{ whiteSpace: "pre-wrap" }}>{entry.description}</Text>
          </RiskField>
          <RiskField label="Supporting quote">
            <Text style={{ whiteSpace: "pre-wrap" }} fs="italic">
              {entry.supportingQuote}
            </Text>
          </RiskField>
          <Group gap="xl" align="flex-start">
            {entry.authorCategory !== null ? (
              <RiskField label="Author category">
                <Text size="sm">{entry.authorCategory}</Text>
              </RiskField>
            ) : null}
            {entry.authorSubcategory !== null ? (
              <RiskField label="Author subcategory">
                <Text size="sm">{entry.authorSubcategory}</Text>
              </RiskField>
            ) : null}
          </Group>
          {entry.documentTitle !== null ? (
            <Text size="xs" c="dimmed">
              {entry.documentTitle}
            </Text>
          ) : null}
        </Stack>
      </ScrollArea>

      <Stack gap="sm">
        {hasSuggestions ? (
          <Group justify="space-between">
            <Text size="xs" c="dimmed">
              Pipeline suggestions shown below.
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
            saveField(
              "validity",
              event.currentTarget.checked ? "not-a-risk" : "ok",
            );
          }}
          disabled={fields.validity.saving}
        />
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
