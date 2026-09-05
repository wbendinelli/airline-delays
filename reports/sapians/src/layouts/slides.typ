#import "../tokens.typ": *
#import "../components/index.typ": *

// Main Slide Engine Initialization (DeepMind & Anthropic Luxury Standard)
#let sapians-slides(
  title: "SAPIANS Presentation",
  author: none,
  aspect-ratio: "16-9",
  body,
) = {
  set document(title: title, author: if author != none { author } else { "SAPIANS" })

  // Page configuration: 16:9 standard ratio (160mm x 90mm)
  set page(
    width: 160mm,
    height: 90mm,
    margin: (x: 10mm, y: 6mm),
    fill: sapians-paper,
  )

  // Typography defaults
  set text(
    font: font-sans,
    fill: sapians-text-dark,
    size: font-size-body,
    lang: "en",
  )

  set par(leading: 0.48em)

  body
}

// Helper: Custom single slide container
#let slide(
  dark: false,
  body,
) = {
  let bg = if dark { sapians-dark } else { sapians-paper }
  let text-fill = if dark { sapians-text-light } else { sapians-text-dark }

  page(fill: bg)[
    #set text(fill: text-fill)
    #body
  ]
}

// -------------------------------------------------------------
// 10 SAPIANS SLIDE FAMILIES (REFINED PROPORTIONS)
// -------------------------------------------------------------

// Family 01: Cover Slide
#let slide-cover(
  title: "",
  subtitle: "",
  author: "",
  affiliation: "",
  dark: true,
) = slide(dark: dark)[
  #place(top + left, dx: 8mm, dy: 20mm)[
    #text(size: font-size-display, weight: "bold", fill: if dark { sapians-text-light } else { sapians-text-dark })[#title]
  ]
  #if subtitle != "" [
    #place(top + left, dx: 8mm, dy: 34mm)[
      #text(size: 11.5pt, weight: "regular", fill: if dark { sapians-text-light } else { sapians-text-dark })[#subtitle]
    ]
  ]
  #place(bottom + left, dx: 8mm, dy: -8mm)[
    #if author != "" [
      #text(size: 8.5pt, weight: "medium", fill: if dark { sapians-muted-light } else { sapians-muted-dark })[#author] \
    ]
    #if affiliation != "" [
      #v(0.8mm)
      #text(size: 7.2pt, weight: "regular", fill: if dark { sapians-muted-light } else { sapians-muted-dark })[#affiliation]
    ]
  ]
]

// Family 02: Problem / Hero Statement Slide
#let slide-problem(
  title: "",
  section: "THE PROBLEM",
  counter: "",
  hero: "",
  subtext: "",
  question: "",
  question-label: "THE QUESTION",
  visual: none,
) = slide(dark: false)[
  #slide-header(title: title, section: section, counter: counter)
  #place(top + left, dx: 2mm, dy: 14mm)[
    #block(width: 66mm)[
      #text(size: font-size-h1, weight: "bold", fill: sapians-text-dark)[#hero]
      #v(2.5mm)
      #text(size: font-size-body, fill: sapians-muted-dark)[#subtext]
      #v(3.5mm)
      #dark-card(
        kicker-title: question-label,
        width: 100%,
        [
          #text(size: 7.8pt, weight: "bold", fill: sapians-text-light)[#question]
        ]
      )
    ]
  ]
  #if visual != none [
    #place(top + left, dx: 74mm, dy: 15mm)[
      #block(width: 66mm)[#visual]
    ]
  ]
]

// Family 03: Definition Split Slide
#let slide-definition(
  title: "",
  section: "DEFINITION",
  counter: "",
  hero: "",
  explanation: "",
  definitions: (),
) = slide(dark: false)[
  #slide-header(title: title, section: section, counter: counter)
  #place(top + left, dx: 2mm, dy: 14mm)[
    #block(width: 64mm)[
      #text(size: font-size-h1, weight: "bold", fill: sapians-text-dark)[#hero]
      #v(3mm)
      #text(size: font-size-body, fill: sapians-muted-dark)[#explanation]
    ]
  ]
  #place(top + left, dx: 72mm, dy: 14mm)[
    #block(width: 68mm)[
      #stack(
        spacing: 2.0mm,
        ..definitions.map(d => def-row(d.at(0), d.at(1), width: 100%))
      )
    ]
  ]
]

// Family 04: Equation Journal Slide
#let slide-equation(
  title: "",
  section: "THE OBJECTIVE",
  counter: "",
  hero: "",
  equation: none,
  steps: (),
) = slide(dark: false)[
  #slide-header(title: title, section: section, counter: counter)
  #place(top + left, dx: 2mm, dy: 14mm)[
    #text(size: font-size-h1, weight: "bold", fill: sapians-text-dark)[#hero]
  ]
  #if equation != none [
    #place(top + left, dx: 2mm, dy: 24mm)[
      #block(
        width: 138mm,
        fill: sapians-code-bg,
        radius: radius-sm,
        stroke: stroke-light,
        inset: (x: 5mm, y: 3.5mm),
      )[
        #align(center)[
          #text(size: 11.5pt, fill: sapians-text-dark)[#equation]
        ]
      ]
    ]
  ]
  #place(top + left, dx: 4mm, dy: 44mm)[
    #block(width: 134mm)[
      #stack(
        spacing: 2.8mm,
        ..steps.enumerate().map(((i, s)) => step-item(i + 1, s))
      )
    ]
  ]
]

// Family 05: Three-Column Mechanism Slide (Model | Code | Idea)
#let slide-three-column(
  title: "",
  section: "HOW IT WORKS",
  counter: "",
  column1-title: "THE MODEL",
  column1-content: none,
  column1-caption: none,
  column2-title: "THE CODE",
  column2-code: none,
  column3-title: "THE IDEA",
  column3-hero: "",
  column3-sub: "",
  column3-footer: "",
) = slide(dark: false)[
  #slide-header(title: title, section: section, counter: counter)
  #place(top + left, dx: 0mm, dy: 11mm)[
    #grid(
      columns: (44mm, 44mm, 48mm),
      gutter: 3.5mm,
      [
        #label(column1-title)
        #v(1.8mm)
        #block(width: 100%, height: 38mm)[#column1-content]
        #if column1-caption != none [
          #v(0.8mm)
          #small-text(column1-caption)
        ]
      ],
      [
        #label(column2-title)
        #v(1.8mm)
        #code-box(width: 100%, height: 50mm)[#column2-code]
      ],
      [
        #label(column3-title)
        #v(1.8mm)
        #dark-card(
          width: 100%,
          height: 50mm,
          [
            #kicker(column3-title)
            #v(4mm)
            #text(size: 8.5pt, weight: "bold", fill: sapians-text-light)[#column3-hero]
            #v(2.5mm)
            #text(size: 6.0pt, fill: sapians-muted-light)[#column3-sub]
            #v(6mm)
            #text(size: 7.2pt, weight: "bold", fill: sapians-text-light)[#column3-footer]
          ]
        )
      ]
    )
  ]
]

// Family 06: Evidence Graph / Full Bleed Slide
#let slide-evidence(
  title: "",
  section: "MECHANISM",
  counter: "",
  hero: "",
  subtext: "",
  graphic: none,
) = slide(dark: false)[
  #slide-header(title: title, section: section, counter: counter)
  #place(top + left, dx: 2mm, dy: 14mm)[
    #block(width: 58mm)[
      #text(size: font-size-h1, weight: "bold", fill: sapians-text-dark)[#hero]
      #v(3mm)
      #text(size: font-size-body, fill: sapians-muted-dark)[#subtext]
    ]
  ]
  #if graphic != none [
    #place(top + left, dx: 64mm, dy: 13mm)[
      #block(width: 76mm)[#graphic]
    ]
  ]
]

// Family 07: Limitation Compare Slide
#let slide-limitation(
  title: "",
  section: "LIMITATIONS",
  counter: "",
  hero: "",
  points: (),
  visual1: none,
  label1: "NARROW",
  sub1: "kernel = 0.20",
  visual2: none,
  label2: "WIDE",
  sub2: "kernel = 0.60",
  conclusion-title: "",
  conclusion-sub: "",
) = slide(dark: false)[
  #slide-header(title: title, section: section, counter: counter)
  #place(top + left, dx: 2mm, dy: 14mm)[
    #block(width: 50mm)[
      #text(size: font-size-h1, weight: "bold", fill: sapians-text-dark)[#hero]
      #v(3mm)
      #stack(
        spacing: 2.2mm,
        ..points.enumerate().map(((i, p)) => step-item(i + 1, p))
      )
    ]
  ]
  #place(top + left, dx: 58mm, dy: 14mm)[
    #block(width: 82mm)[
      #grid(
        columns: (1fr, 1fr),
        gutter: 3.5mm,
        [
          #block(width: 100%)[#visual1]
          #v(0.8mm)
          #kicker(label1) #h(1.5mm) #small-text(sub1)
        ],
        [
          #block(width: 100%)[#visual2]
          #v(0.8mm)
          #kicker(label2) #h(1.5mm) #small-text(sub2)
        ]
      )
      #v(2.5mm)
      #text(size: 7.5pt, weight: "bold", fill: sapians-text-dark)[#conclusion-title]
      #v(0.8mm)
      #text(size: 6.0pt, fill: sapians-muted-dark)[#conclusion-sub]
    ]
  ]
]

// Family 08: Contrast Slide (Not This vs This)
#let slide-contrast(
  title: "",
  section: "INTERPRETATION",
  counter: "",
  hero: "",
  not-this-content: "",
  this-content: "",
  not-this-label: "NOT THIS",
  this-label: "THIS",
  this-sub: "LOCAL ≠ GLOBAL",
) = slide(dark: false)[
  #slide-header(title: title, section: section, counter: counter)
  #place(top + left, dx: 2mm, dy: 14mm)[
    #text(size: font-size-h1, weight: "bold", fill: sapians-text-dark)[#hero]
  ]
  #place(top + left, dx: 2mm, dy: 28mm)[
    #block(width: 138mm)[
      #contrast-pair(
        not-this-content,
        this-content,
        not-this-label: not-this-label,
        this-label: this-label,
        this-sub: this-sub,
      )
    ]
  ]
]

// Family 09: Dark Takeaway Slide
#let slide-takeaway(
  title: "",
  section: "CONCLUSION",
  counter: "",
  hero: "",
  subtext: "",
  takeaway-title: "KEY TAKEAWAY",
  takeaway-text: "",
) = slide(dark: true)[
  #slide-header(title: title, section: section, counter: counter, dark: true)
  #place(top + left, dx: 2mm, dy: 16mm)[
    #block(width: 68mm)[
      #text(size: 13.5pt, weight: "bold", fill: sapians-text-light)[#hero]
      #v(2.5mm)
      #text(size: 7.0pt, fill: sapians-muted-light)[#subtext]
    ]
  ]
  #place(top + left, dx: 74mm, dy: 16mm)[
    #block(width: 64mm)[
      #block(
        fill: rgb("221F1C"),
        stroke: stroke-dark,
        radius: radius-sm,
        inset: 4.0mm,
        width: 100%,
      )[
        #kicker(takeaway-title, dark: true)
        #v(2.5mm)
        #text(size: 9.0pt, weight: "bold", fill: sapians-text-light)[#takeaway-text]
      ]
    ]
  ]
]

// Family 10: Component Index / Summary Slide
#let slide-index(
  title: "SAPIANS",
  section: "ROADMAP",
  counter: "",
  items: (),
) = slide(dark: false)[
  #slide-header(title: title, section: section, counter: counter)
  #place(top + left, dx: 2mm, dy: 14mm)[
    #grid(
      columns: (1fr, 1fr),
      gutter: 5mm,
      ..items.map(item => block(
        fill: sapians-white,
        stroke: stroke-light,
        radius: radius-sm,
        inset: 3.0mm,
        width: 100%,
        [
          #grid(
            columns: (auto, 1fr),
            gutter: 2.5mm,
            kicker(item.at(0)),
            [
              #text(size: 7.5pt, weight: "bold", fill: sapians-text-dark)[#item.at(1)]
              #if item.len() > 2 [
                #v(0.8mm)
                #text(size: 6.0pt, fill: sapians-muted-dark)[#item.at(2)]
              ]
            ]
          )
        ]
      ))
    )
  ]
]
