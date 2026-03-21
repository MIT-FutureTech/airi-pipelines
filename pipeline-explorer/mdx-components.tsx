import type { MDXComponents } from "mdx/types";
import { NodeLink } from "@/components/NodeLink";

export function useMDXComponents(
  components: MDXComponents,
): MDXComponents {
  return {
    ...components,
    NodeLink,
  };
}
