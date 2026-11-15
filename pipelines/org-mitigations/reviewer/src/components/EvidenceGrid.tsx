import { Stack, Table, Text, Tooltip, UnstyledButton } from "@mantine/core";
import { type CellSelection, cellKey } from "@/lib/cells";
import {
  type Decision,
  DISCLOSURE_LABELS,
  DISCLOSURE_MARKS,
  type Disclosure,
} from "@/lib/decisions";
import { STRENGTH_COLORS, strongest } from "@/lib/strength";
import type { Company, Domain, LocatedEvidence, Locus } from "@/lib/types";

interface EvidenceGridProps {
  companies: Company[];
  taxonomy: Locus[];
  cells: Map<string, LocatedEvidence[]>;
  decisions: Map<string, Decision>;
  selection: CellSelection | null;
  onSelect: (selection: CellSelection) => void;
}

export function EvidenceGrid({
  companies,
  taxonomy,
  cells,
  decisions,
  selection,
  onSelect,
}: EvidenceGridProps) {
  const domains = taxonomy.flatMap((locus) => locus.domains);
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
                <Table.Th colSpan={locus.domains.length} ta="center">
                  {locus.name}
                </Table.Th>
              </Tooltip>
            ))}
          </Table.Tr>
          <Table.Tr>
            {domains.map((domain) => (
              <Tooltip
                key={domain.code}
                label={<DomainDefinition domain={domain} />}
                multiline
                w={360}
              >
                <Table.Th fw="normal">
                  {`${domain.code} ${domain.short_name}`}
                </Table.Th>
              </Tooltip>
            ))}
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {companies.map((company) => (
            <Table.Tr key={company.company_id}>
              <Table.Th scope="row">{company.name}</Table.Th>
              {domains.map((domain) => {
                const key = cellKey(company.company_id, domain.code);
                return (
                  <GridCell
                    key={domain.code}
                    evidence={cells.get(key)}
                    disclosure={decisions.get(key)?.disclosure ?? null}
                    isSelected={
                      selection?.company.company_id === company.company_id &&
                      selection.domain.code === domain.code
                    }
                    onSelect={(evidence) =>
                      onSelect({ company, domain, evidence })
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
  evidence: LocatedEvidence[] | undefined;
  disclosure: Disclosure | null;
  isSelected: boolean;
  onSelect: (evidence: LocatedEvidence[]) => void;
}

function GridCell({
  evidence,
  disclosure,
  isSelected,
  onSelect,
}: GridCellProps) {
  if (evidence === undefined) {
    return <Table.Td />;
  }
  const strength = strongest(evidence);
  const quotes =
    evidence.length === 1 ? "1 quote" : `${evidence.length} quotes`;
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
        aria-label={`${quotes}, strongest ${strength}, ${decided}`}
        onClick={() => onSelect(evidence)}
      >
        {disclosure === null
          ? evidence.length
          : `${evidence.length} ${DISCLOSURE_MARKS[disclosure]}`}
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

function DomainDefinition({ domain }: { domain: Domain }) {
  return (
    <Stack gap={4}>
      <Text fw={600}>{`${domain.code} ${domain.name}`}</Text>
      <Text>{domain.definition}</Text>
      <Text>{`Examples: ${domain.examples.join("; ")}`}</Text>
    </Stack>
  );
}
