import { Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useSuitability } from "@/lib/suitability/store";

export function AddSourceDialog() {
  const { addKnowledgeSource } = useSuitability();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [fileName, setFileName] = useState("");

  const ref = url.trim() || fileName;

  const submit = () => {
    if (!name.trim() || !ref) return;
    addKnowledgeSource({ name: name.trim(), ref, connected: true });
    toast.success(`${name.trim()} added as a knowledge source`);
    setName("");
    setUrl("");
    setFileName("");
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger className="mt-2 flex w-full items-center gap-2 rounded-sm border border-dashed border-border px-2.5 py-1.5 text-xs text-muted-foreground transition-colors hover:border-gold hover:text-gold">
        <Plus className="size-3.5" /> Add source
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add a knowledge source</DialogTitle>
          <DialogDescription>
            Connect an internal document or wiki space. Indexing runs before answers cite it.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="src-name">Source name</Label>
            <Input
              id="src-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Cross-Border Rulebook"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="src-url">URL</Label>
            <Input
              id="src-url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://intranet.juliusbaer.com/..."
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="src-file">Or upload a document</Label>
            <Input
              id="src-file"
              type="file"
              onChange={(e) => setFileName(e.target.files?.[0]?.name ?? "")}
              className="text-xs"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={!name.trim() || !ref}>
            Add
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
