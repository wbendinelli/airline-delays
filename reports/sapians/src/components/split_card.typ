#import "../tokens.typ": *

// Numbered Key Item (e.g. 01 Approximate the model...)
#let step-item(
  number,
  title,
  description: none,
  dark: false,
) = {
  let num-str = if type(number) == int {
    if number < 10 { "0" + str(number) } else { str(number) }
  } else {
    str(number)
  }
  let title-fill = if dark { sapians-text-light } else { sapians-text-dark }
  let desc-fill = if dark { sapians-muted-light } else { sapians-muted-dark }

  grid(
    columns: (auto, 1fr),
    gutter: 3.5mm,
    align: (top + left, top + left),
    text(fill: sapians-terracotta, size: 6.8pt, weight: "bold")[#num-str],
    [
      #text(fill: title-fill, size: 6.8pt, weight: if description != none { "bold" } else { "medium" })[#title]
      #if description != none [
        #v(0.6mm)
        #text(fill: desc-fill, size: 5.8pt)[#description]
      ]
    ]
  )
}

// Definition row (e.g. [BLACK BOX] -> f(x))
#let def-row(
  kicker-text,
  value-text,
  width: 100%,
) = {
  block(
    width: width,
    fill: sapians-card-bg,
    radius: radius-sm,
    stroke: stroke-light,
    inset: (x: 3.5mm, y: 2.0mm),
  )[
    #grid(
      columns: (1fr, auto),
      align: (horizon + left, horizon + right),
      text(fill: sapians-terracotta, size: font-size-kicker, weight: "bold", tracking: 0.12em)[#upper(kicker-text)],
      text(fill: sapians-text-dark, size: 6.8pt, weight: "bold")[#value-text]
    )
  ]
}

// Contrast Comparison: Not This vs This (Refined Proportions)
#let contrast-pair(
  not-this-content,
  this-content,
  not-this-label: "NOT THIS",
  this-label: "THIS",
  this-sub: "LOCAL ≠ GLOBAL",
) = {
  grid(
    columns: (1fr, 1fr),
    gutter: 5mm,
    // NOT THIS (Subtle card with diagonal cancel or muted style)
    block(
      width: 100%,
      height: 34mm,
      fill: sapians-card-bg,
      radius: radius-sm,
      stroke: stroke-light,
      inset: 3.5mm,
      [
        #text(fill: sapians-muted-dark, size: font-size-kicker, weight: "bold", tracking: 0.14em)[#upper(not-this-label)]
        #v(4.5mm)
        #text(fill: sapians-muted-dark, size: 8.5pt, weight: "bold")[#not-this-content]
        #v(3.5mm)
        #line(length: 100%, stroke: 1.0pt + sapians-terracotta)
      ]
    ),
    // THIS (Dark card with high contrast)
    block(
      width: 100%,
      height: 34mm,
      fill: sapians-dark,
      radius: radius-sm,
      inset: 3.5mm,
      [
        #text(fill: sapians-terracotta, size: font-size-kicker, weight: "bold", tracking: 0.14em)[#upper(this-label)]
        #v(4.5mm)
        #text(fill: sapians-text-light, size: 8.5pt, weight: "bold")[#this-content]
        #if this-sub != none [
          #v(3.5mm)
          #text(fill: sapians-muted-light, size: 5.2pt, weight: "bold", tracking: 0.12em)[#upper(this-sub)]
        ]
      ]
    )
  )
}
