# Vendored Parser Module

> **Internal module** — This is an implementation detail of bossanova.
> Users should not import from this module directly. Use the model classes
> (`lm`, `glm`, `lmer`, `glmer`) which handle formula parsing automatically.

This module contains formula parsing code vendored and adapted from the
[**formulae**](https://github.com/bambinos/formulae) library.

## Attribution

**Original Project:** formulae
**Author:** Tomás Capretto ([@tomicapretto](https://github.com/tomicapretto))
**Repository:** https://github.com/bambinos/formulae
**License:** MIT

The formulae library implements Wilkinson's formulas for mixed-effects models,
extending classical statistical formulas to support group-specific effects
(random effects). It was developed to support
[Bambi](https://github.com/bambinos/bambi), a Bayesian GLMM package.

## Modifications

The vendored code has been adapted for bossanova's needs:

- Simplified to include only the scanner, parser, and AST node definitions
- Removed dependencies on external packages (numpy, etc.)
- Type annotations added/updated for strict type checking
- Integrated with bossanova's formula evaluation infrastructure

## License

The original formulae code is licensed under the MIT License:

```
MIT License

Copyright (c) bambinos developers

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

bossanova is also licensed under the MIT License. See the project root
[LICENSE](../../LICENSE) file for details.
