#import "../tokens.typ": *

// SAPIANS Precision Code Box Component
#let code-box(
  body,
  width: 100%,
  height: auto,
  title: none,
  lang: none,
  dark: false,
) = {
  let bg-color = if dark { sapians-code-bg-dark } else { sapians-code-bg }
  let border-stroke = if dark { stroke-dark } else { stroke-light }
  let text-fill = if dark { sapians-text-light } else { sapians-text-dark }

  block(
    width: width,
    height: height,
    fill: bg-color,
    radius: radius-sm,
    stroke: border-stroke,
    inset: (x: 3.0mm, y: 3.0mm),
    clip: true,
  )[
    #if title != none [
      #grid(
        columns: (1fr, auto),
        align: (left, right),
        text(fill: if dark { sapians-muted-light } else { sapians-muted-dark }, size: 5.0pt, weight: "bold", tracking: 0.12em)[#upper(title)],
        if lang != none { text(fill: sapians-terracotta, size: 5.0pt, weight: "bold")[#lang] }
      )
      #v(1.2mm)
      #line(length: 100%, stroke: border-stroke)
      #v(1.2mm)
    ]
    #set text(font: font-mono, size: font-size-code, fill: text-fill)
    #set par(leading: 0.42em)
    #body
  ]
}
