import { Stack, Table, Text, Tooltip, UnstyledButton } from "@mantine/core";
import { type CellSelection, cellKey, cellQuotes } from "@/lib/cells";
import { type CodeGroup, fullLabel, shortLabel } from "@/lib/codes";
import {
  type Decision,
  DISCLOSURE_LABELS,
  DISCLOSURE_MARKS,
  type Disclosure,
} from "@/lib/decisions";
import { STRENGTH_COLORS, strongest } from "@/lib/strength";
import type { Code, Company, Mitigation, Quote } from "@/lib/types";

interface EvidenceGridProps {
  companies: Company[];
  groups: CodeGroup[];
  cells: Map<string, Mitigation[]>;
  quotes: Map<string, Quote[]>;
  decisions: Map<string, Decision>;
  selection: CellSelection | null;
  onSelect: (selection: CellSelection) => void;
}

export function EvidenceGrid({
  companies,
  groups,
  cells,
  quotes,
  decisions,
  selection,
  onSelect,
}: EvidenceGridProps) {
  const codes = groups.flatMap((group) => group.codes);
  return (
    <Table.ScrollContainer minWidth={1100}>
      <Table withTableBorder withColumnBorders>
        <Table.Thead>
          <Table.Tr>
            <Table.Th rowSpan={2}>Company</Table.Th>
            {groups.map((group) => (
              <Table.Th
                key={group.codes[0].record_id}
                colSpan={group.codes.length}
                ta="center"
              >
                {group.name}
              </Table.Th>
            ))}
          </Table.Tr>
          <Table.Tr>
            {codes.map((code) => (
              <Tooltip
                key={code.record_id}
                label={<CodeDefinition code={code} />}
                multiline
                w={360}
              >
                <Table.Th fw="normal">{shortLabel(code)}</Table.Th>
              </Tooltip>
            ))}
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {companies.map((company) => (
            <Table.Tr key={company.company_id}>
              <Table.Th scope="row">{company.name}</Table.Th>
              {codes.map((code) => {
                const key = cellKey(company.company_id, code.record_id);
                const mitigations = cells.get(key);
                return (
                  <GridCell
                    key={code.record_id}
                    mitigations={mitigations}
                    quotes={
                      mitigations === undefined
                        ? []
                        : cellQuotes(mitigations, quotes)
                    }
                    disclosure={decisions.get(key)?.disclosure ?? null}
                    isSelected={
                      selection?.company.company_id === company.company_id &&
                      selection.code.record_id === code.record_id
                    }
                    onSelect={(selected) =>
                      onSelect({ company, code, mitigations: selected })
                    }
                  />
                );
              })}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Table.ScrollContainer>
  );
}

const SELECTED_OUTLINE = "inset 0 0 0 3px currentColor";

interface GridCellProps {
  mitigations: Mitigation[] | undefined;
  quotes: Quote[];
  disclosure: Disclosure | null;
  isSelected: boolean;
  onSelect: (mitigations: Mitigation[]) => void;
}

function GridCell({
  mitigations,
  quotes,
  disclosure,
  isSelected,
  onSelect,
}: GridCellProps) {
  if (mitigations === undefined) {
    return <Table.Td />;
  }
  const strength = strongest(quotes);
  const count =
    mitigations.length === 1
      ? "1 mitigation"
      : `${mitigations.length} mitigations`;
  const decided =
    disclosure === null
      ? "undecided"
      : `decided ${DISCLOSURE_LABELS[disclosure]}`;
  return (
    <Table.Td
      p={0}
      style={{
        ...STRENGTH_COLORS[strength],
        boxShadow: isSelected ? SELECTED_OUTLINE : undefined,
      }}
    >
      <UnstyledButton
        w="100%"
        py="xs"
        fz="sm"
        ta="center"
        aria-pressed={isSelected}
        aria-label={`${count}, strongest quote ${strength}, ${decided}`}
        onClick={() => onSelect(mitigations)}
      >
        {disclosure === null
          ? mitigations.length
          : `${mitigations.length} ${DISCLOSURE_MARKS[disclosure]}`}
      </UnstyledButton>
    </Table.Td>
  );
}

function CodeDefinition({ code }: { code: Code }) {
  return (
    <Stack gap={4}>
      <Text fw={600}>{fullLabel(code)}</Text>
      <Text>{code.definition}</Text>
      {code.details !== null && (
        <Text style={{ whiteSpace: "pre-line" }}>{code.details}</Text>
      )}
    </Stack>
  );
}
