document$.subscribe(({ body }) => { 
  renderMathInElement(body, {
    delimiters: [
      { left: "$$",  right: "$$",  display: true },
      { left: "$",   right: "$",   display: false },
      { left: "\\(", right: "\\)", display: false },
      { left: "\\[", right: "\\]", display: true },
      // marimo renders math inside its own HTML outputs (e.g. mo.md() nested
      // in a layout helper) with these delimiters instead.
      { left: "||(", right: "||)", display: false },
      { left: "||[", right: "||]", display: true },
    ],
  })
})
