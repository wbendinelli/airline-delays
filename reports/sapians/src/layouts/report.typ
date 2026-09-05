#import "../tokens.typ": *
#import "../components/index.typ": *

// SAPIANS Technical Report & Memo Layout (Crisp White Edition)
#let sapians-report(
  title: "SAPIANS Technical Report",
  subtitle: none,
  author: "SAPIANS Team",
  date: none,
  version: "1.0",
  body,
) = {
  set document(title: title, author: author)

  let formatted-date = if date != none { date } else { datetime.today().display("[day]/[month]/[year]") }

  set page(
    paper: "a4",
    margin: (x: 25mm, top: 25mm, bottom: 25mm),
    fill: sapians-paper,
    header: context [
      #if counter(page).get().first() > 1 [
        #grid(
          columns: (1fr, auto),
          text(size: 7.5pt, fill: sapians-muted-dark, weight: "medium")[#title],
          text(size: 7.5pt, fill: sapians-muted-dark)[#formatted-date]
        )
        #v(1.0mm)
        #line(length: 100%, stroke: stroke-light)
      ]
    ],
    footer: context [
      #grid(
        columns: (1fr, auto),
        text(size: 7.5pt, fill: sapians-muted-dark)[SAPIANS Research & Development],
        text(size: 7.5pt, fill: sapians-muted-dark, weight: "bold")[#counter(page).display()]
      )
    ]
  )

  set text(
    font: font-sans,
    fill: sapians-text-dark,
    size: 9.0pt,
    lang: "pt",
  )

  set par(justify: true, leading: 0.60em)

  // Document Title Header
  block(width: 100%, inset: (bottom: 5mm))[
    #text(fill: sapians-terracotta, size: 7.5pt, weight: "bold", tracking: 0.15em)[SAPIANS TECHNICAL REPORT]
    #v(1.5mm)
    #text(fill: sapians-text-dark, size: 20pt, weight: "bold")[#title]
    #if subtitle != none [
      #v(1.0mm)
      #text(fill: sapians-muted-dark, size: 11pt)[#subtitle]
    ]
    #v(2.5mm)
    #line(length: 100%, stroke: 0.5pt + sapians-line)
    #v(2.0mm)
    #grid(
      columns: (1fr, 1fr, 1fr),
      text(size: 8.0pt)[*Autor:* #author],
      text(size: 8.0pt)[*Data:* #formatted-date],
      align(right)[#text(size: 8.0pt)[*Versão:* #version]],
    )
    #v(4.0mm)
  ]

  body
}
