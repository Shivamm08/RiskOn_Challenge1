import { FileSpreadsheet, FileText } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useSuitability } from "@/lib/suitability/store";
import type { SourceFileType } from "@/lib/suitability/types";

const MOCK_TABLE = {
  columns: ["Booking centre", "Client category", "Product class", "Permitted", "Review"],
  rows: [
    ["CH", "Private/Retail", "Capital protected", "Yes", "2026-04-30"],
    ["CH", "Private/Retail", "Leveraged certificates", "No", "2026-04-30"],
    ["Monaco", "Professional", "Yield enhancement", "Yes", "2026-06-15"],
    ["Germany", "Professional", "Structured notes", "Conditional", "2026-07-01"],
    ["EEA", "Institutional", "All classes", "Yes", "2026-05-20"],
  ],
};

export function SourcePreviewDialog() {
  const { previewSource, closePreview } = useSuitability();
  const type: SourceFileType = previewSource?.fileType ?? "doc";
  const tabular = type === "excel" || type === "csv";

  return (
    <Dialog open={!!previewSource} onOpenChange={(o) => !o && closePreview()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-start gap-2 text-left text-base leading-snug">
            {tabular ? (
              <FileSpreadsheet className="mt-0.5 size-4 shrink-0 text-gold" />
            ) : (
              <FileText className="mt-0.5 size-4 shrink-0 text-gold" />
            )}
            {previewSource?.page_title}
          </DialogTitle>
          <DialogDescription>
            {type.toUpperCase()} preview · demo content, not the live file
          </DialogDescription>
        </DialogHeader>

        {tabular ? (
          <div className="max-h-[60vh] overflow-auto rounded-sm border border-border">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr className="bg-surface-2">
                  {MOCK_TABLE.columns.map((c) => (
                    <th
                      key={c}
                      className="label-xs border-b border-border px-3 py-2 text-left text-muted-foreground"
                    >
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {MOCK_TABLE.rows.map((row) => (
                  <tr key={row.join()} className="border-b border-border last:border-0">
                    {row.map((cell) => (
                      <td key={cell} className="px-3 py-2">
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="max-h-[60vh] overflow-auto rounded-sm border border-border bg-surface-2 px-6 py-6">
            <p className="label-xs text-gold">Julius Baer · Internal</p>
            <h3 className="mt-2 font-display text-lg leading-snug">
              {previewSource?.page_title}
            </h3>
            <div className="mt-4 space-y-3 font-display text-[15px] leading-relaxed">
              <p className="border-l-2 border-gold pl-3">{previewSource?.excerpt}</p>
              <p className="text-muted-foreground">
                1. Scope. This section applies to all relationships booked in the centres listed
                in the annex, irrespective of the client&apos;s domicile at onboarding.
              </p>
              <p className="text-muted-foreground">
                2. Assessment. The Relationship Manager records the assessment outcome before
                order release. Where an alert remains open, the client instruction is documented
                verbatim in the advisory record.
              </p>
              <p className="text-muted-foreground">
                3. Review. This document is reviewed semi-annually by the Suitability Expert
                team. Pending amendments are marked &quot;under review&quot; in the annex.
              </p>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
