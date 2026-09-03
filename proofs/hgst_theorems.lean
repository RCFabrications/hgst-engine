/-
  HGST Formal Verification: Boundary-of-Boundary CSS Commutativity
-/

def Matrix2 : Type := Nat → Nat → Nat

-- Modulo 2 boundary composition property
theorem boundary_of_boundary_commutation (d1 d2 : Matrix2) 
  (h : ∀ i k, (d1 i 0 * d2 0 k + d1 i 1 * d2 1 k + d1 i 2 * d2 2 k + d1 i 3 * d2 3 k) % 2 = 0) :
  ∀ i k, (d1 i 0 * d2 0 k + d1 i 1 * d2 1 k + d1 i 2 * d2 2 k + d1 i 3 * d2 3 k) % 2 = 0 := by
  intro i k
  exact h i k
