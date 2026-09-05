#import "../tokens.typ": *
#import "../components/index.typ": *

// SAPIANS Scientific Article / Paper Layout (Crisp White Edition)
#let sapians-article(
  title: "SAPIANS Scientific Article",
  abstract: none,
  authors: (),
  keywords: (),
  body,
) = {
  set document(title: title, author: authors.map(a => if type(a) == str { a } else { a.name }))

  set page(
    paper: "a4",
    margin: (x: 20mm, top: 22mm, bottom: 22mm),
    fill: sapians-paper,
    footer: context [
      #grid(
        columns: (1fr, auto),
        text(size: 7.2pt, fill: sapians-muted-dark)[SAPIANS Journal of Applied AI & Design],
        text(size: 7.2pt, fill: sapians-muted-dark, weight: "bold")[#counter(page).display()]
      )
    ]
  )

  set text(
    font: font-sans,
    fill: sapians-text-dark,
    size: 8.8pt,
    lang: "pt",
  )

  set par(justify: true, leading: 0.58em)

  // Paper Title Header
  align(center)[
    #text(fill: sapians-terracotta, size: 7.5pt, weight: "bold", tracking: 0.15em)[SAPIANS RESEARCH ARTICLE]
    #v(2.5mm)
    #text(fill: sapians-text-dark, size: 17pt, weight: "bold")[#title]
    #v(3.5mm)
    #if authors.len() > 0 [
      #grid(
        columns: authors.len(),
        gutter: 8mm,
        ..authors.map(a => {
          if type(a) == str [
            #text(size: 8.5pt, weight: "bold")[#a]
          ] else [
            #text(size: 8.5pt, weight: "bold")[#a.name] \
            #if "affiliation" in a [ #text(size: 7.2pt, fill: sapians-muted-dark)[#a.affiliation] ]
          ]
        })
      )
    ]
    #v(3.5mm)
  ]

  if abstract != none [
    #align(center)[
      #block(width: 90%, fill: sapians-card-bg, radius: radius-sm, stroke: stroke-light, inset: 3.5mm)[
        #align(left)[
          #text(weight: "bold", size: 8.0pt, fill: sapians-text-dark)[Resumo] \
          #v(1.2mm)
          #text(size: 7.6pt, fill: sapians-muted-dark)[#abstract]
          #if keywords.len() > 0 [
            #v(1.8mm)
            #text(size: 7.2pt)[*Palavras-chave:* #keywords.join(", ")]
          ]
        ]
      ]
    ]
    #v(3.5mm)
  ]

  // Two column layout for paper body
  show heading: it => [
    #v(2mm)
    #text(fill: sapians-text-dark, weight: "bold", size: 10pt)[#it.body]
    #v(1mm)
  ]

  columns(2, gutter: 5mm)[
    #body
  ]
}
