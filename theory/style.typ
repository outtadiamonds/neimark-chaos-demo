// Общее оформление теории: PDF формата A4 и страницы-картинки для показа в программе.
#let target = sys.inputs.at("target", default: "pdf")

#let setup(lang, body) = {
  set document(title: if lang == "ru" { "Осциллятор Неймарка: динамический хаос и корреляционная функция" } else { "Neimark oscillator: dynamic chaos and the correlation function" })
  set text(lang: lang, font: ("New Computer Modern", "Libertinus Serif"), size: 11.5pt)
  set page(
    ..if target == "png" { (width: 17cm, height: 24cm, margin: (x: 1.3cm, y: 1.2cm)) } else { (paper: "a4", margin: (x: 2.2cm, y: 2cm)) },
    numbering: if target == "png" { none } else { "1" },
  )
  set par(justify: true, leading: 0.62em, first-line-indent: 0em, spacing: 0.9em)
  set heading(numbering: "1.")
  show heading.where(level: 1): it => block(above: 1.4em, below: 0.8em, text(size: 14pt, it))
  show heading.where(level: 2): it => block(above: 1.1em, below: 0.6em, text(size: 12pt, it))
  set math.equation(numbering: "(1)", supplement: none)
  set enum(indent: 0.6em)
  set list(indent: 0.6em)
  set table(stroke: 0.5pt + luma(150), inset: 6pt)
  show table: set par(justify: false)
  show table: set text(size: 10.5pt)
  show figure.caption: set text(size: 10.5pt)
  body
}

#let title(main, sub) = align(center)[
  #text(size: 19pt, weight: "bold", main) \
  #v(0.2em)
  #text(size: 13pt, sub)
  #v(0.8em)
]

// Термин при первом появлении
#let term(body) = emph(strong(body))
