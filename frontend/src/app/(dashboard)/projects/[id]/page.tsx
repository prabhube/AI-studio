/**
 * Project Detail Page — /projects/[id]
 *
 * WHY this page exists:
 *   Shows all assets belonging to a project:
 *     - Videos tab
 *     - Images tab
 *     - Audio tab
 *     - Settings tab (rename, delete project)
 *
 * The [id] dynamic segment is the project UUID.
 *
 * Implementation: Phase 2.
 */

export default function ProjectDetailPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Project: {params.id}</h1>
      <p className="text-white/40 text-sm">
        Implementation: Phase 2 — Project detail view
      </p>
    </div>
  );
}
