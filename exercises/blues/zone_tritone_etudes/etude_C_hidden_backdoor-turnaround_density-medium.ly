\version "2.24.0"
\header {
  title = "12-Bar Etude — Hidden — Backdoor:Turnaround — Medium"
  subtitle = "Zone–Tritone Engine: Hidden Blues / Bluesy Toggle"
  composer = "Generated"
}

global = {
  \time 4/4
  \tempo 4 = 92
}

chords = \chordmode {
  c:71 c:71 c:71 c:71 f:71 f:71 c:71 c:71 g:71 f:71 c:71 bes:71 c:71 c:71 c:71 c:71 f:71 f:71 c:71 c:71 g:71 f:71 c:71 bes:71 c:71 c:71
}

melody = \relative c' {
  \global
  \tuplet 3/2 { c8 c8 f8 ees8 g8 g8 bes8 c'8 ges8 e8 f8 bes8 } | \tuplet 3/2 { c'8 bes8 ges8 e8 e8 c8 bes,8 g,8 f,8 bes,8 f,8 c,8 } | \tuplet 3/2 { g,8 ees,8 bes,8 a,8 ges,8 c,8 e,8 e,8 f,8 f,8 ges,8 bes,8 } | \tuplet 3/2 { bes,8 e,8 c,8 e,8 c,8 f,8 bes,8 ees8 a,8 g,8 c8 c8 } | \tuplet 3/2 { c8 d8 d8 c8 aes,8 b,8 f,8 aes,8 a,8 b,8 ees8 a,8 } | \tuplet 3/2 { f,8 a,8 d8 b,8 ees8 d8 a,8 ees,8 aes,8 f,8 aes,8 f,8 } | \tuplet 3/2 { g,8 ees,8 ges,8 g,8 ees,8 f,8 c,8 bes,8 bes,8 bes,8 e,8 g,8 } | \tuplet 3/2 { e,8 ges,8 e,8 g,8 bes,8 ees8 e8 f8 ees8 bes,8 g,8 bes,8 } | \tuplet 3/2 { f,8 g,8 bes,8 e,8 f,8 c,8 f,8 b,8 g,8 d,8 des,8 b,8 } | \tuplet 3/2 { c8 a,8 bes,8 bes,8 bes,8 d8 c8 a,8 f,8 f,8 d,8 c,8 } | \tuplet 3/2 { bes,8 c8 e8 f8 e8 g8 e8 ges8 c8 ges,8 ges,8 e,8 } | \tuplet 3/2 { d,8 e,8 ees,8 f,8 e,8 e,8 bes,8 g,8 bes,8 g,8 d,8 f,8 } | \tuplet 3/2 { e,8 ges,8 ges,8 bes,8 g,8 g,8 bes,8 ges,8 bes,8 e,8 bes,8 c8 } | \tuplet 3/2 { bes,8 ees8 ges8 e8 ees8 bes,8 c8 g,8 e,8 ges,8 f,8 e,8 } | \tuplet 3/2 { c,8 f,8 ees,8 bes,8 a,8 f,8 e,8 e,8 e,8 c,8 f,8 c,8 } | \tuplet 3/2 { g,8 f,8 e,8 ees,8 g,8 a,8 g,8 g,8 bes,8 ges,8 a,8 bes,8 } | \tuplet 3/2 { f,8 d,8 ees,8 ees,8 ees,8 aes,8 a,8 b,8 d8 f8 bes8 a8 } | \tuplet 3/2 { c'8 f'8 d'8 a8 aes8 f8 a8 d'8 bes8 a8 b8 f8 } | \tuplet 3/2 { e8 ges8 bes8 a8 ges8 e8 g8 f8 f8 g8 bes8 g8 } | \tuplet 3/2 { g8 ees8 g8 bes8 c'8 a8 g8 ges8 g8 ees8 f8 e8 } | \tuplet 3/2 { d8 d8 des8 g,8 des,8 f,8 f,8 g,8 c8 g,8 bes,8 g,8 } | \tuplet 3/2 { c8 b,8 ees8 a,8 d8 aes,8 a,8 ees,8 bes,8 c8 b,8 c8 } | \tuplet 3/2 { c8 g,8 bes,8 bes,8 ees8 ees8 bes,8 f,8 ees,8 f,8 f,8 c,8 } | \tuplet 3/2 { d,8 bes,8 des8 aes,8 bes,8 g,8 aes,8 g,8 des,8 des,8 e,8 aes,8 } | e,1 | c,1
}

\score {
  <<
    \new ChordNames \chords
    \new Staff \melody
  >>
  \layout {}
  \midi {}
}
