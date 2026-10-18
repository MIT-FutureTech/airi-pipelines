import { Stack, Table, Text, Tooltip, UnstyledButton } from "@mantine/core";
import { type CellSelection, cellKey } from "@/lib/cells";
import { STRENGTH_COLORS, strongest } from "@/lib/strength";
import type { Code, Company, LocatedEvidence, Locus } from "@/lib/types";

interface EvidenceGridProps {
  companies: Company[];
  taxonomy: Locus[];
  cells: Map<string, LocatedEvidence[]>;
  selection: CellSelection | null;
  onSelect: (selection: CellSelection) => void;
}

export function EvidenceGrid({
  companies,
  taxonomy,
  cells,
  selection,
  onSelect,
}: EvidenceGridProps) {
  const codes = taxonomy.flatMap((locus) => locus.codes);
  return (
    <Table.ScrollContainer minWidth={1100}>
      <Table withTableBorder withColumnBorders>
        <Table.Thead>
          <Table.Tr>
            <Table.Th rowSpan={2}>Company</Table.Th>
            {taxonomy.map((locus) => (
              <Tooltip
                key={locus.code}
                label={<LocusDefinition locus={locus} />}
                multiline
                w={360}
              >
                <Table.Th colSpan={locus.codes.length} ta="center">
                  {locus.name}
                </Table.Th>
              </Tooltip>
            ))}
          </Table.Tr>
          <Table.Tr>
            {codes.map((code) => (
              <Tooltip
                key={code.code}
                label={<CodeDefinition code={code} />}
                multiline
                w={360}
              >
                <Table.Th fw="normal">
                  {`${code.code} ${code.short_name}`}
                </Table.Th>
              </Tooltip>
            ))}
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {companies.map((company) => (
            <Table.Tr key={company.company_id}>
              <Table.Th scope="row">{company.name}</Table.Th>
              {codes.map((code) => (
                <GridCell
                  key={code.code}
                  evidence={cells.get(cellKey(company.company_id, code.code))}
                  isSelected={
                    selection?.company.company_id === company.company_id &&
                    selection.code.code === code.code
                  }
                  onSelect={(evidence) => onSelect({ company, code, evidence })}
                />
              ))}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Table.ScrollContainer>
  );
}

const SELECTED_OUTLINE = "inset 0 0 0 3px currentColor";

interface GridCellProps {
  evidence: LocatedEvidence[] | undefined;
  isSelected: boolean;
  onSelect: (evidence: LocatedEvidence[]) => void;
}

function GridCell({ evidence, isSelected, onSelect }: GridCellProps) {
  if (evidence === undefined) {
    return <Table.Td />;
  }
  return (
    <Table.Td
      p={0}
      style={{
        ...STRENGTH_COLORS[strongest(evidence)],
        boxShadow: isSelected ? SELECTED_OUTLINE : undefined,
      }}
    >
      <UnstyledButton
        w="100%"
        py="xs"
        fz="sm"
        ta="center"
        aria-pressed={isSelected}
        onClick={() => onSelect(evidence)}
      >
        {evidence.length}
      </UnstyledButton>
    </Table.Td>
  );
}

function LocusDefinition({ locus }: { locus: Locus }) {
  return (
    <Stack gap={4}>
      <Text fw={600}>{locus.name}</Text>
      <Text>{locus.definition}</Text>
    </Stack>
  );
}

function CodeDefinition({ code }: { code: Code }) {
  return (
    <Stack gap={4}>
      <Text fw={600}>{`${code.code} ${code.name}`}</Text>
      <Text>{code.definition}</Text>
      <Text>{`Examples: ${code.examples.join("; ")}`}</Text>
    </Stack>
  );
}
