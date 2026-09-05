#import "../tokens.typ": *

// SAPIANS Precision Slide Header (DeepMind / Anthropic style)
#let slide-header(
  title: "",
  section: "",
  counter: "",
  dark: false,
) = {
  let text-color = if dark { sapians-text-light } else { sapians-text-dark }
  let muted-color = if dark { sapians-muted-light } else { sapians-muted-dark }
  let line-color = if dark { sapians-line-dark } else { sapians-line }

  place(top + left, dx: 0mm, dy: 0mm)[
    #block(width: 100%, inset: (bottom: 2mm))[
      #grid(
        columns: (1fr, auto),
        align: (bottom + left, bottom + right),
        [
          #text(fill: text-color, size: 9.5pt, weight: "bold")[#title]
          #if section != "" [
            #h(4.5mm)
            #text(fill: muted-color, size: 5.2pt, weight: "medium", tracking: 0.14em)[#upper(section)]
          ]
        ],
        [
          #if counter != "" [
            #text(fill: muted-color, size: 5.2pt, weight: "medium", tracking: 0.08em)[#counter]
          ]
        ]
      )
      #v(2.0mm)
      #line(length: 100%, stroke: 0.25pt + line-color)
    ]
  ]
}

// Micro Kicker tag in Terracotta
#let kicker(text-content, dark: false) = {
  text(fill: sapians-terracotta, size: 5.2pt, weight: "bold", tracking: 0.14em)[#upper(text-content)]
}

// Label in Muted tone
#let label(text-content, dark: false) = {
  let col = if dark { sapians-muted-light } else { sapians-muted-dark }
  text(fill: col, size: 5.2pt, weight: "bold", tracking: 0.12em)[#upper(text-content)]
}

// Small secondary text
#let small-text(text-content, dark: false) = {
  let col = if dark { sapians-muted-light } else { sapians-muted-dark }
  text(fill: col, size: 6.0pt)[#text-content]
}
