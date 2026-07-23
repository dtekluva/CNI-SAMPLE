import { useEffect, useState } from "react";

export type Entity = { id: number; legal_name: string };
export type Selection = { id: number | "group"; legal_name: string };

/**
 * Entity switcher (FR-ENT-2). Lists only the entities the API returns — which is
 * already permission-scoped server-side (T-B6), so there is no client-side leak.
 * A "Group" option appears only when more than one entity is visible.
 */
export function EntitySwitcher({ onSelect }: { onSelect?: (s: Selection) => void }) {
  const [entities, setEntities] = useState<Entity[]>([]);
  const [selected, setSelected] = useState<string>("group");

  useEffect(() => {
    fetch("/api/entities/")
      .then((r) => (r.ok ? r.json() : []))
      .then((data: unknown) => setEntities(Array.isArray(data) ? (data as Entity[]) : []))
      .catch(() => setEntities([]));
  }, []);

  const showGroup = entities.length > 1;

  function choose(value: string) {
    setSelected(value);
    if (value === "group") {
      onSelect?.({ id: "group", legal_name: "Group" });
    } else {
      const ent = entities.find((e) => String(e.id) === value);
      if (ent) onSelect?.({ id: ent.id, legal_name: ent.legal_name });
    }
  }

  return (
    <div className="ns-field">
      <label className="ns-field__label" htmlFor="entity-switcher">
        Entity
      </label>
      <select
        id="entity-switcher"
        className="ns-input"
        value={selected}
        onChange={(e) => choose(e.target.value)}
      >
        {showGroup && <option value="group">Group (all entities)</option>}
        {entities.map((e) => (
          <option key={e.id} value={String(e.id)}>
            {e.legal_name}
          </option>
        ))}
      </select>
    </div>
  );
}
