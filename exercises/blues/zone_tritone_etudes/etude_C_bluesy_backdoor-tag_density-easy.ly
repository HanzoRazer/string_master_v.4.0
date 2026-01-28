\version "2.24.0"
\header {
  title = "12-Bar Etude — Bluesy — Backdoor:Tag — Easy"
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
  f8 c8 bes,8 ges,8 f,8 c,8 c,8 ees,8 | a,8 e,8 a,8 f,8 ges,8 f,8 ges,8 ges,8 | c,8 ges,8 bes,8 f,8 ges,8 ees,8 ees,8 ges,8 | a,8 c8 e8 e8 a8 ees8 ges8 bes8 | d'8 f'8 bes'8 d'8 d'8 a8 aes8 aes8 | aes8 ees8 b,8 bes,8 b,8 f,8 aes,8 b,8 | f,8 g,8 bes,8 f,8 ges,8 f,8 g,8 ees,8 | g,8 f,8 a,8 f,8 a,8 f,8 e,8 ges,8 | d,8 e,8 b,8 g,8 des,8 des,8 f,8 des,8 | a,8 c8 ees8 bes,8 b,8 c8 d8 b,8 | e8 des8 aes,8 ees,8 f,8 bes,8 bes,8 des8 | f8 c8 bes,8 a,8 g,8 ges,8 ees,8 bes,8 | ges,8 g,8 e,8 g,8 ges,8 e,8 c,8 ges,8 | ges,8 bes,8 ges,8 f,8 g,8 ees,8 c,8 ees,8 | a,8 a,8 bes,8 ges,8 c,8 e,8 ees,8 ees,8 | ges,8 c,8 f,8 bes,8 ges,8 f,8 a,8 ees,8 | b,8 b,8 ees8 aes8 d8 f8 f8 b,8 | aes,8 b,8 d8 aes,8 d,8 c,8 bes,8 ees8 | c8 ges,8 bes,8 ees8 ges8 c8 c8 bes,8 | a,8 g,8 g,8 f,8 g,8 e,8 bes,8 ges,8 | des,8 b,8 bes,8 c8 c8 f8 g8 bes8 | aes8 a8 bes8 d'8 c'8 bes8 c'8 aes8 | g8 bes8 ees'8 aes'8 e'8 bes8 aes8 aes8 | e8 a8 bes8 ees'8 ees'8 bes8 a8 bes8 | ees'1 | c'1
}

\score {
  <<
    \new ChordNames \chords
    \new Staff \melody
  >>
  \layout {}
  \midi {}
}
