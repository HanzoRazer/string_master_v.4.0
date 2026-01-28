\version "2.24.0"
\header {
  title = "12-Bar Etude — Hidden — Backdoor:Turnaround — Easy"
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
  e8 ees8 ees8 ees8 e8 a8 f8 g8 | bes8 ees'8 c'8 bes8 c'8 c'8 e'8 c'8 | bes8 ees'8 e'8 f'8 g'8 ees'8 e'8 g'8 | bes'8 bes'8 bes'8 f'8 e'8 e'8 ges'8 bes'8 | c'8 c'8 f'8 d'8 a8 a8 ees8 ees8 | f8 c8 b,8 ees8 f8 c8 f8 f8 | g8 bes8 a8 g8 c'8 g8 ees8 c8 | c8 ges,8 f,8 a,8 c8 a,8 e,8 bes,8 | d8 d8 f8 b,8 g,8 c8 g,8 f,8 | a,8 aes,8 b,8 c8 a,8 f,8 ees,8 ees,8 | bes,8 a,8 c8 f8 bes8 ges8 c8 bes,8 | d8 f8 bes8 aes8 d8 f8 aes8 bes8 | c'8 bes8 g8 ees8 g8 bes8 e8 c8 | e8 g8 ees8 g8 c'8 g8 e8 c8 | e8 g8 e8 bes,8 e,8 a,8 ees,8 g,8 | g,8 e,8 g,8 ges,8 g,8 ees,8 f,8 c,8 | a,8 f,8 c,8 f,8 f,8 a,8 a,8 c8 | c8 d8 f8 a8 a8 d'8 a8 ees8 | g8 f8 ees8 e8 bes,8 e,8 e,8 bes,8 | g,8 f,8 g,8 a,8 e,8 ges,8 bes,8 c8 | b,8 g,8 b,8 b,8 b,8 bes,8 d8 b,8 | f,8 f,8 b,8 aes,8 ees,8 f,8 bes,8 ees8 | bes,8 bes,8 e,8 g,8 e,8 e,8 a,8 g,8 | f,8 ees,8 ees,8 bes,8 d8 f8 ees8 aes8 | e1 | c1
}

\score {
  <<
    \new ChordNames \chords
    \new Staff \melody
  >>
  \layout {}
  \midi {}
}
