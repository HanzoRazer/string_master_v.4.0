\version "2.24.0"
\header {
  title = "12-Bar Etude — Bluesy — Backdoor:Tag — Hard"
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
  f16 ees16 ees16 ges16 c16 bes,16 c16 ges,16 e,16 ees,16 a,16 ges,16 g,16 ges,16 bes,16 ees16 | c16 ges,16 bes,16 a,16 bes,16 ees16 g16 ees16 ges16 f16 g16 f16 ges16 a16 a16 ges16 | ees16 f16 c16 a,16 bes,16 ges,16 f,16 ges,16 c,16 ees,16 a,16 ges,16 a,16 ges,16 e,16 bes,16 | bes,16 ees16 ees16 c16 a,16 c16 ges,16 f,16 ees,16 ges,16 f,16 ges,16 g,16 ges,16 f,16 ees,16 | b,16 bes,16 f,16 ees,16 aes,16 d,16 a,16 bes,16 d16 bes,16 a,16 a,16 d16 a,16 b,16 aes,16 | f,16 d,16 bes,16 aes,16 a,16 ees,16 c,16 b,16 f,16 aes,16 a,16 c16 aes,16 c16 aes,16 ees,16 | ges,16 ges,16 bes,16 a,16 ges,16 bes,16 f,16 f,16 f,16 ees,16 g,16 e,16 f,16 ges,16 e,16 ees,16 | ees,16 ees,16 a,16 f,16 e,16 e,16 a,16 ees,16 ees,16 ges,16 f,16 bes,16 ees16 a,16 bes,16 bes,16 | bes,16 bes,16 d16 d16 bes,16 e,16 des,16 f,16 e,16 c,16 c,16 bes,16 bes,16 c16 f16 bes16 | bes16 a16 d'16 b16 a16 f16 d16 b,16 c16 f16 aes16 bes16 d'16 c'16 d'16 b16 | e'16 e'16 e'16 des'16 f'16 d'16 d'16 g'16 g'16 bes'16 bes'16 e'16 ees'16 e'16 des'16 aes16 | f16 f16 g16 f16 ees16 c16 g,16 ges,16 g,16 ges,16 g,16 ges,16 a,16 f,16 a,16 ges,16 | ges,16 e,16 bes,16 ees16 a,16 g,16 e,16 bes,16 ges,16 ges,16 e,16 g,16 ges,16 ges,16 c,16 bes,16 | g,16 ees,16 a,16 e,16 bes,16 a,16 bes,16 f,16 a,16 ees,16 ges,16 c,16 g,16 c16 e16 bes,16 | ees16 bes,16 e,16 e,16 e,16 bes,16 ges,16 bes,16 a,16 e,16 ees,16 ges,16 f,16 a,16 c16 ges,16 | ges,16 c,16 bes,16 a,16 f,16 a,16 ges,16 f,16 c,16 ees,16 g,16 e,16 bes,16 e,16 c,16 ges,16 | d,16 a,16 c16 c16 aes,16 b,16 c16 a,16 d16 aes,16 ees,16 ees,16 d,16 ees,16 bes,16 ees16 | aes16 a16 bes16 bes16 b16 aes16 b16 bes16 aes16 b16 bes16 d'16 f'16 aes'16 b'16 b'16 | f'16 e'16 ees'16 g'16 c'16 bes16 bes16 g16 g16 a16 e16 f16 e16 f16 a16 ees16 | f16 ges16 g16 a16 bes16 bes16 a16 ges16 ees16 a,16 bes,16 g,16 ges,16 c,16 e,16 bes,16 | g,16 g,16 bes,16 f,16 f,16 bes,16 d16 bes,16 bes,16 d16 bes,16 bes,16 c16 c16 bes,16 des16 | aes,16 f,16 bes,16 ees16 aes16 bes16 c'16 d'16 b16 aes16 d16 ees16 f16 c16 f16 ees16 | g16 d16 bes,16 aes,16 g,16 aes,16 des16 ees16 ees16 e16 d16 aes,16 e,16 ees,16 e,16 des,16 | ges,16 f,16 g,16 a,16 ges,16 c,16 bes,16 c16 ees16 bes,16 e,16 bes,16 ees16 a,16 a,16 bes,16 | ees1 | c1
}

\score {
  <<
    \new ChordNames \chords
    \new Staff \melody
  >>
  \layout {}
  \midi {}
}
