/**
 * 元素の CPK カラーと表示半径（3D描画用）
 * 半径は視覚的にボンドが見えるよう実際のvdW半径より小さく設定
 */

export const ELEMENT_COLORS = {
  H:  0xFFFFFF,
  C:  0x505050,
  N:  0x3050F8,
  O:  0xFF2010,
  F:  0x90E050,
  S:  0xFFFF30,
  Cl: 0x1FF01F,
  P:  0xFF8000,
  B:  0xFFB5B5,
  Xe: 0x429EB0,
  Pt: 0xD4AF37,
  Fe: 0xE06633,
  // 架空配置用
  A:  0xFF8C00,   // orange
  B:  0x00CED1,   // dark turquoise
  C_: 0xFF1493,   // deep pink
  D:  0x32CD32,   // lime green
  X:  0x9B59B6,   // purple (center)
};

export const ELEMENT_RADII = {
  H:  0.22,
  C:  0.34,
  N:  0.33,
  O:  0.32,
  F:  0.30,
  S:  0.42,
  Cl: 0.40,
  P:  0.44,
  B:  0.36,
  Xe: 0.50,
  Pt: 0.52,
  Fe: 0.46,
  A:  0.36,
  B_: 0.36,  // 'B' element name conflicts; use B for turquoise
  C_: 0.36,
  D:  0.36,
  X:  0.28,
};

export function getColor(element) {
  return ELEMENT_COLORS[element] ?? 0xAAAAAA;
}

export function getRadius(element) {
  return ELEMENT_RADII[element] ?? 0.35;
}
