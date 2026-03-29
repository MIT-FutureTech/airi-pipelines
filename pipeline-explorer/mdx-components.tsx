import type { MDXComponents } from "mdx/types";
import { NodeLink } from "@/pipeline/components/NodeLink";

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
    ...components,
    // biome-ignore lint/style/useNamingConvention: MDX component mappings require PascalCase
    NodeLink,
  };
}
