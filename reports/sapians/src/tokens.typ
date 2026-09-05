// SAPIANS Design Tokens
// Modern typography-driven scientific publishing & slide system
// Crisp White Edition (Google DeepMind & Apple Precision Standards)

// Core Color Palette
#let sapians-dark = rgb("161311")
#let sapians-paper = rgb("FFFFFF")          // Crisp Pure White Canvas
#let sapians-card-bg = rgb("F8F8FA")       // Subtle Elevated Card Fill
#let sapians-text-dark = rgb("161311")     // Deep Charcoal Primary Text
#let sapians-text-light = rgb("EDEBDC")    // Warm Off-White for Dark Canvas
#let sapians-muted-dark = rgb("6D675F")    // Secondary Text & Annotations
#let sapians-muted-light = rgb("A9A498")   // Secondary Text on Dark
#let sapians-terracotta = rgb("C96F3F")    // Exclusive Visual Intervention Accent
#let sapians-line = rgb("E5E0D8")          // Crisp Hairline Dividing Rules (0.25pt)
#let sapians-line-dark = rgb("3A342E")     // Hairlines on Dark Canvas
#let sapians-code-bg = rgb("F6F5F2")       // Code Box Container Background
#let sapians-code-bg-dark = rgb("201C19")  // Dark Code Box Background
#let sapians-blue-data = rgb("315B86")     // Primary Scientific Data Blue
#let sapians-amber = rgb("D9822B")         // Secondary Scientific Series
#let sapians-sage = rgb("4E8752")          // Tertiary Scientific Series
#let sapians-white = rgb("FFFFFF")

// Typography Font Families
#let font-sans = ("Inter", "Helvetica Neue", "Arial")
#let font-serif = ("Charter", "Times New Roman")
#let font-mono = ("JetBrains Mono", "Menlo", "Courier New")

// Calibrated Typographic Scale (16:9 Presentation: 160mm x 90mm)
#let font-size-display = 28pt     // Cover title
#let font-size-h1 = 13pt          // Slide main title
#let font-size-h2 = 10.5pt        // Secondary header
#let font-size-h3 = 8.5pt         // Hero card text
#let font-size-body = 6.8pt       // Standard slide body
#let font-size-small = 5.8pt      // Secondary annotations
#let font-size-kicker = 5.2pt     // Uppercase tracking kickers
#let font-size-code = 5.5pt       // Monospace code listings

// Slide Dimensions (16:9 Presentation Standard)
#let slide-width = 160mm
#let slide-height = 90mm
#let slide-margin-x = 10mm
#let slide-margin-y = 6mm

// Standard Radii & Precision Strokes (0.25pt Hairlines)
#let radius-sm = 1.2mm
#let radius-md = 2.0mm
#let radius-lg = 3.5mm
#let stroke-light = 0.25pt + sapians-line
#let stroke-dark = 0.25pt + sapians-line-dark
#let stroke-accent = 0.75pt + sapians-terracotta
