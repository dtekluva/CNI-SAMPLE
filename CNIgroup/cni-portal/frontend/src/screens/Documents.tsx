import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet } from "../api/client";
import { useApi } from "../api/useApi";
import { Badge, Button, CellTitle, EmptyState, PageHeader, SearchBox, Table } from "../ui";

type Doc = {
  id: number;
  title: string;
  access_mode: string;
  committee: string;
  topic: string;
  page_count: number;
  is_late: boolean;
  created_at: string;
};

async function download(id: number) {
  try {
    const r = await apiGet<{ url: string }>(`/documents/${id}/download/`);
    const a = document.createElement("a");
    a.href = r.url;
    a.target = "_blank";
    a.rel = "noopener";
    a.click();
  } catch {
    /* view-only or error — server enforces */
  }
}

export function DocumentsScreen() {
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  useEffect(() => {
    const t = setTimeout(() => setDebounced(q.trim()), 250);
    return () => clearTimeout(t);
  }, [q]);

  const path = debounced ? `/documents/search/?q=${encodeURIComponent(debounced)}` : "/documents/";
  const { data, loading, error } = useApi<Doc[]>(path);
  const docs = Array.isArray(data) ? data : [];
  const navigate = useNavigate();

  return (
    <div>
      <PageHeader title="Documents" sub="The entity document library — versioned, watermarked, access-controlled. Click a row to read." />
      <div className="ns-toolbar">
        <SearchBox value={q} onChange={setQ} placeholder="Search titles and paper contents…" />
        <span className="ns-count">
          {loading ? "Searching…" : `${docs.length} document${docs.length === 1 ? "" : "s"}${debounced ? ` matching “${debounced}”` : ""}`}
        </span>
      </div>
      {error && <Badge tone="danger">{error}</Badge>}
      {docs.length > 0 && (
        <Table head={<><th>Document</th><th>Topic</th><th className="is-num">Pages</th><th>Access</th><th /></>}>
          {docs.map((d) => (
            <tr key={d.id} style={{ cursor: "pointer" }} onClick={() => navigate(`/documents/${d.id}`)}>
              <td>
                <CellTitle
                  title={
                    <>
                      {d.title} {d.is_late && <Badge tone="warning">Late</Badge>}
                    </>
                  }
                  meta={new Date(d.created_at).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}
                />
              </td>
              <td className="ns-muted">{d.topic || d.committee || "—"}</td>
              <td className="is-num ns-muted">{d.page_count}</td>
              <td>
                <Badge tone={d.access_mode === "downloadable" ? "success" : "neutral"}>
                  {d.access_mode === "downloadable" ? "Downloadable" : "View only"}
                </Badge>
              </td>
              <td className="is-num">
                {d.access_mode === "downloadable" && (
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={(e) => {
                      e.stopPropagation();
                      download(d.id);
                    }}
                  >
                    Download
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </Table>
      )}
      {!loading && docs.length === 0 && (
        debounced ? (
          <EmptyState title={`No documents match “${debounced}”`} hint="Search covers titles and the text of the papers you can access." />
        ) : (
          <EmptyState title="No documents yet" hint="Board papers and packs you can access will appear here." />
        )
      )}
    </div>
  );
}
