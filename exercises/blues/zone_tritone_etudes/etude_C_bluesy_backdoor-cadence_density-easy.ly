\version "2.24.0"
\header {
  title = "12-Bar Etude — Bluesy — Backdoor:Cadence — Easy"
  subtitle = "Zone–Tritone Engine: Hidden Blues / Bluesy Toggle"
  composer = "Generated"
}

global = {
  \time 4/4
  \tempo 4 = 92
}

chords = \chordmode {
  c:71 c:71 c:71 c:71 f:71 f:71 c:71 c:71 g:71 f:71 bes:71 c:71 c:71 c:71 c:71 c:71 f:71 f:71 c:71 c:71 g:71 f:71 bes:71 c:71 c:71 c:71
}

melody = \relative c' {
  \global
  e8 f8 c8 bes,8 ges,8 c,8 ees,8 ees,8 | c,8 g,8 bes,8 bes,8 ges,8 bes,8 e,8 ges,8 | ges,8 c,8 ges,8 e,8 a,8 bes,8 c8 ges,8 | a,8 g,8 bes,8 e,8 ges,8 bes,8 c8 ges,8 | aes,8 ees,8 b,8 b,8 aes,8 d,8 c,8 b,8 | b,8 d8 bes,8 aes,8 bes,8 b,8 c8 b,8 | a,8 ges,8 e,8 e,8 ees,8 f,8 f,8 ees,8 | ges,8 c,8 bes,8 ges,8 ees,8 ges,8 ges,8 ges,8 | e,8 g,8 f,8 bes,8 bes,8 f,8 c,8 des,8 | d,8 b,8 aes,8 c8 aes,8 a,8 c8 ees8 | f8 bes8 g8 aes8 e8 f8 g8 aes8 | g8 e8 ees8 f8 ees8 bes,8 g,8 ees,8 | ges,8 bes,8 ges,8 bes,8 ges,8 ges,8 a,8 bes,8 | a,8 a,8 g,8 ges,8 bes,8 bes,8 g,8 ges,8 | a,8 ges,8 c,8 ees,8 ges,8 ges,8 f,8 ges,8 | c,8 bes,8 c8 e8 ees8 bes,8 g,8 ees,8 | b,8 bes,8 a,8 d8 b,8 b,8 ees8 b,8 | bes,8 ees8 b,8 a,8 bes,8 b,8 ees8 aes8 | a8 g8 g8 e8 ges8 c8 ees8 ges8 | g8 a8 e8 ees8 c8 a,8 f,8 ees,8 | des,8 b,8 c8 bes,8 c8 des8 bes,8 des8 | aes,8 ees,8 d,8 aes,8 c8 c8 d8 ees8 | g8 aes8 ees8 ees8 ees8 des8 ees8 aes8 | ges8 ges8 c8 c8 f8 ges8 e8 bes,8 | ees1 | c1
}

\score {
  <<
    \new ChordNames \chords
    \new Staff \melody
  >>
  \layout {}
  \midi {}
}
