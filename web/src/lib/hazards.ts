// The standard oilfield hazards checklist.
// MUST stay in sync with HAZARD_ITEMS in services/field_ticket.py so the
// PDF generator recognizes every item drivers can tick.
export const HAZARD_ITEMS = [
  "H2S present",
  "High pressure lines",
  "Slippery surfaces / spills",
  "Heavy equipment movement",
  "Chemical / fluid exposure",
  "Fire / explosion risk",
  "Overhead power lines",
  "Confined space",
  "Lease road traffic",
  "Overweight load risk",
  "Other (see notes)",
] as const;
