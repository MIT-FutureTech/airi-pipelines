---
paths:
  - "toolbox-lib/**"
---

# Toolbox Guidelines

## Private Members

Default to private (`_`-prefixed) for members, methods, and free functions. If the public interface needs expanding, do so thoughtfully — simply removing the underscore is usually not the best design.

Tests may freely access private attributes of the class under test.
