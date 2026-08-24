import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Plus } from "lucide-react";
import { useNavigate, useParams } from "react-router";
import { Modal, NeonButton } from "@/components/ui";
import { NewNoteModal } from "./components/NewNoteModal";
import { NoteEditor } from "./components/NoteEditor";
import { NoteList } from "./components/NoteList";
import { NoteSearchBar } from "./components/NoteSearchBar";
import { useNote, useNotes } from "./hooks";

function useDebounced<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}

export function KnowledgeVaultPage() {
  const { noteId } = useParams<{ noteId?: string }>();
  const navigate = useNavigate();

  const [searchInput, setSearchInput] = useState("");
  const q = useDebounced(searchInput, 300);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [newNoteOpen, setNewNoteOpen] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [pendingNoteId, setPendingNoteId] = useState<string | null>(null);

  const { data: notes, isLoading } = useNotes({ q, tags: selectedTags });
  const { data: note } = useNote(noteId);

  const availableTags = useMemo(() => {
    const names = new Set<string>();
    for (const n of notes ?? []) {
      for (const tag of n.tags) names.add(tag.slug);
    }
    return Array.from(names).sort();
  }, [notes]);

  function requestSelect(id: string) {
    if (isDirty && id !== noteId) {
      setPendingNoteId(id);
      return;
    }
    navigate(`/notes/${id}`);
  }

  function confirmDiscard() {
    if (pendingNoteId) {
      setIsDirty(false);
      navigate(`/notes/${pendingNoteId}`);
      setPendingNoteId(null);
    }
  }

  function toggleTag(tag: string) {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  }

  const showEditorOnMobile = Boolean(noteId);

  return (
    <div className="mx-auto flex max-w-[1440px] flex-col gap-8 p-4 md:p-8 lg:p-16">
      <header className="flex flex-col gap-2 border-b border-surface-container-highest pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-mono text-label-mono text-neon-lime uppercase">
            Secure Data Storage // Sector 7G
          </p>
          <h1 className="font-display text-headline-lg text-on-surface uppercase tracking-tight">
            Knowledge Vault
          </h1>
        </div>
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          Sys: Online <span className="mx-2 text-on-surface-variant">|</span> Uplink: Active
        </p>
      </header>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <section
          className={`flex flex-col gap-4 lg:col-span-4 ${showEditorOnMobile ? "hidden lg:flex" : "flex"}`}
        >
          <div className="flex items-center justify-between gap-2">
            <h2 className="font-display text-title-sm text-on-surface uppercase">Data Shards</h2>
            <NeonButton
              type="button"
              onClick={() => setNewNoteOpen(true)}
              className="!px-3 !py-1.5"
            >
              <Plus size={14} aria-hidden="true" />
              New
            </NeonButton>
          </div>
          <NoteSearchBar
            value={searchInput}
            onChange={setSearchInput}
            availableTags={availableTags}
            selectedTags={selectedTags}
            onToggleTag={toggleTag}
          />
          {isLoading ? (
            <p className="font-mono text-label-mono text-on-surface-variant uppercase">
              &gt;&gt; loading shards...
            </p>
          ) : (
            <NoteList notes={notes ?? []} selectedId={noteId} onSelect={requestSelect} />
          )}
        </section>

        <section
          className={`lg:col-span-8 ${showEditorOnMobile ? "flex flex-col gap-4" : "hidden lg:flex lg:flex-col lg:gap-4"}`}
        >
          <button
            type="button"
            onClick={() => navigate("/notes")}
            className="flex items-center gap-1 font-mono text-label-mono text-on-surface-variant uppercase hover:text-neon-lime lg:hidden"
          >
            <ArrowLeft size={14} aria-hidden="true" /> Back
          </button>

          {!noteId ? (
            <p className="border border-dashed border-outline-variant p-6 text-center font-mono text-label-mono text-on-surface-variant uppercase">
              Select a shard to view its contents
            </p>
          ) : note ? (
            <NoteEditor key={note.id} note={note} onDirtyChange={setIsDirty} />
          ) : (
            <p className="font-mono text-label-mono text-on-surface-variant uppercase">
              &gt;&gt; decrypting shard...
            </p>
          )}
        </section>
      </div>

      <NewNoteModal
        open={newNoteOpen}
        onClose={() => setNewNoteOpen(false)}
        onCreated={(id) => navigate(`/notes/${id}`)}
      />

      <Modal
        open={pendingNoteId !== null}
        onClose={() => setPendingNoteId(null)}
        title="Unsaved Changes"
      >
        <div className="flex flex-col gap-5">
          <p className="font-body text-body-md text-on-surface-variant">
            This shard has unsaved edits. Switching now will discard them.
          </p>
          <div className="flex justify-end gap-3">
            <NeonButton type="button" variant="ghost" onClick={() => setPendingNoteId(null)}>
              Keep Editing
            </NeonButton>
            <NeonButton type="button" variant="secondary" onClick={confirmDiscard}>
              Discard Changes
            </NeonButton>
          </div>
        </div>
      </Modal>
    </div>
  );
}
