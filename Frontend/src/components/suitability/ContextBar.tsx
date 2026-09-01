import { ChevronDown, SlidersHorizontal } from "lucide-react";
import { useState } from "react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSuitability } from "@/lib/suitability/store";
import {
  BOOKING_CENTRES,
  CLIENT_CATEGORIES,
  SERVICE_MODELS,
  type QueryContext,
} from "@/lib/suitability/types";
import { cn } from "@/lib/utils";

function Field<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: T | undefined;
  options: readonly T[];
  onChange: (value: T | undefined) => void;
}) {
  return (
    <label className="block min-w-0 flex-1">
      <span className="label-xs mb-1.5 block text-muted-foreground">{label}</span>
      <Select
        value={value ?? "__any"}
        onValueChange={(v) => onChange(v === "__any" ? undefined : (v as T))}
      >
        <SelectTrigger className="w-full bg-surface-2 text-sm">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__any">Not specified</SelectItem>
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}

export function ContextBar() {
  const { context, setContext } = useSuitability();
  const [open, setOpen] = useState(false);

  const applied = [context.bookingCentre, context.clientCategory, context.serviceModel].filter(
    Boolean,
  ) as string[];

  const patch = <K extends keyof QueryContext>(key: K, value: QueryContext[K]) => {
    const next: QueryContext = { ...context };
    if (value === undefined) delete next[key];
    else next[key] = value;
    setContext(next);
  };


  return (
    <div className="rounded-md border border-border bg-surface">
      <div className="flex items-center justify-between gap-3 px-3 py-2">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          className="label-xs flex items-center gap-1.5 text-muted-foreground transition-colors hover:text-foreground"
        >
          <SlidersHorizontal className="size-3.5" />
          Context
          <ChevronDown className={cn("size-3.5 transition-transform", open && "rotate-180")} />
        </button>

        <div className="flex min-w-0 items-center gap-2">
          {applied.length > 0 ? (
            <>
              <span className="truncate rounded-sm border border-gold/40 bg-cream px-2 py-1 text-[11px] font-medium text-cream-foreground">
                Context applied · {applied.join(" · ")}
              </span>
              <button
                type="button"
                onClick={() => setContext({})}
                className="label-xs text-muted-foreground hover:text-foreground"
              >
                Clear
              </button>
            </>
          ) : (
            <span className="text-[11px] text-muted-foreground">Optional — refines the answer</span>
          )}
        </div>
      </div>

      {open && (
        <div className="flex flex-col gap-3 border-t border-border px-3 py-3 sm:flex-row">
          <Field
            label="Booking centre"
            value={context.bookingCentre}
            options={BOOKING_CENTRES}
            onChange={(v) => patch("bookingCentre", v)}
          />
          <Field
            label="Client category"
            value={context.clientCategory}
            options={CLIENT_CATEGORIES}
            onChange={(v) => patch("clientCategory", v)}
          />
          <Field
            label="Service model"
            value={context.serviceModel}
            options={SERVICE_MODELS}
            onChange={(v) => patch("serviceModel", v)}

          />
        </div>
      )}
    </div>
  );
}
