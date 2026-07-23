/** Northstar icon set — 24px grid, 1.75 stroke, inherits currentColor. */
const PATHS: Record<string, string> = {
  dashboard: "M4 4h7v7H4zM13 4h7v4h-7zM13 11h7v9h-7zM4 14h7v6H4z",
  building: "M5 21V5a1 1 0 0 1 1-1h7a1 1 0 0 1 1 1v16M14 9h4a1 1 0 0 1 1 1v11M3 21h18M8 8h2M8 12h2M8 16h2",
  calendar: "M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zM16 3v4M8 3v4M4 10h16",
  minutes: "M7 3h10a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM9.5 8h5M9.5 12h5M9.5 16h3",
  gavel: "M13 6l5 5M4 21h9M9.5 3.5l7 7-3 3-7-7zM14 14l6 6",
  folder: "M3 6a1 1 0 0 1 1-1h5l2 2h9a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1z",
  check: "M20 6L9 17l-5-5",
  checks: "M8 12l3 3 7-7M3 12l3 3",
  bell: "M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6M10.5 20a2 2 0 0 0 3 0",
  shield: "M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z",
  settings: "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM19 12a7 7 0 0 0-.1-1.2l2-1.5-2-3.5-2.4 1a7 7 0 0 0-2-1.2L14 3h-4l-.5 2.6a7 7 0 0 0-2 1.2l-2.4-1-2 3.5 2 1.5A7 7 0 0 0 5 12c0 .4 0 .8.1 1.2l-2 1.5 2 3.5 2.4-1a7 7 0 0 0 2 1.2L10 21h4l.5-2.6a7 7 0 0 0 2-1.2l2.4 1 2-3.5-2-1.5c.06-.4.1-.8.1-1.2z",
  registers: "M4 19V5a2 2 0 0 1 2-2h13v18H6a2 2 0 0 1-2-2zM19 17H6a2 2 0 0 0-2 2M8 7h7",
  people: "M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM2.5 20c.5-3.5 3-5.5 6.5-5.5s6 2 6.5 5.5M16 4.6a3.5 3.5 0 0 1 0 6.8M18.5 14.9c1.7.8 2.8 2.2 3 5.1",
  key: "M15 7a3 3 0 1 1-2.8 4H9v2H7v2H4v-3l5.2-5.2A3 3 0 0 1 15 7zM16 8h.01",
  clipboard: "M9 4h6v3H9zM9 4a2 2 0 0 0-2 2H6a1 1 0 0 0-1 1v13a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V7a1 1 0 0 0-1-1h-1a2 2 0 0 0-2-2M9 12l2 2 4-4",
  logout: "M14 12H3M10 8l4 4-4 4M14 4h5a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-5",
  search: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-4.3-4.3",
};

export function Icon({ name }: { name: keyof typeof PATHS | string }) {
  const d = PATHS[name] ?? PATHS.folder;
  return (
    <svg className="ns-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={d} />
    </svg>
  );
}
