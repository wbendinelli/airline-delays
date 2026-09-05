#import "../tokens.typ": *

// SAPIANS Dark Callout Card (DeepMind High Contrast)
#let dark-card(
  body,
  kicker-title: none,
  width: 100%,
  height: auto,
  inset: 3.2mm,
) = {
  block(
    width: width,
    height: height,
    fill: sapians-dark,
    radius: radius-sm,
    inset: inset,
  )[
    #if kicker-title != none [
      #text(fill: sapians-terracotta, size: font-size-kicker, weight: "bold", tracking: 0.14em)[#upper(kicker-title)]
      #v(1.6mm)
    ]
    #set text(fill: sapians-text-light, size: font-size-body)
    #body
  ]
}

// SAPIANS Light Card with subtle elevation & hairline border
#let light-card(
  body,
  kicker-title: none,
  width: 100%,
  height: auto,
  inset: 3.2mm,
  fill: sapians-card-bg,
  stroke: stroke-light,
) = {
  block(
    width: width,
    height: height,
    fill: fill,
    radius: radius-sm,
    stroke: stroke,
    inset: inset,
  )[
    #if kicker-title != none [
      #text(fill: sapians-terracotta, size: font-size-kicker, weight: "bold", tracking: 0.14em)[#upper(kicker-title)]
      #v(1.6mm)
    ]
    #set text(fill: sapians-text-dark, size: font-size-body)
    #body
  ]
}

// Terracotta Accent Card / Callout
#let accent-card(
  body,
  title: none,
  width: 100%,
) = {
  block(
    width: width,
    fill: sapians-card-bg,
    stroke: (left: 1.8pt + sapians-terracotta, rest: stroke-light),
    radius: (right: radius-sm),
    inset: (x: 2.8mm, y: 2.2mm),
  )[
    #if title != none [
      #text(fill: sapians-terracotta, size: 6.2pt, weight: "bold")[#title]
      #v(0.8mm)
    ]
    #set text(size: font-size-body)
    #body
  ]
}
