import { Stack, Table, Text, Tooltip } from "@mantine/core";
import { cellKey } from "@/lib/cells";
import { STRENGTH_COLORS, strongest } from "@/lib/strength";
import type { Code, Company, LocatedEvidence, Locus } from "@/lib/types";

interface EvidenceGridProps {
  companies: Company[];
  taxonomy: Locus[];
  cells: Map<string, LocatedEvidence[]>;
}

export function EvidenceGrid({
  companies,
  taxonomy,
  cells,
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
                />
              ))}
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </Table.ScrollContainer>
  );
}

function GridCell({ evidence }: { evidence: LocatedEvidence[] | undefined }) {
  if (evidence === undefined) {
    return <Table.Td />;
  }
  return (
    <Table.Td ta="center" style={STRENGTH_COLORS[strongest(evidence)]}>
      {evidence.length}
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
