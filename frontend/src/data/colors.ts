export const colors = {
  primary: '#BD1872',
  dark: '#232527',
  light: '#D4DCFF',
  accent: '#7D83FF',
  blue: '#007FFF',
} as const

export type ColorKey = keyof typeof colors
