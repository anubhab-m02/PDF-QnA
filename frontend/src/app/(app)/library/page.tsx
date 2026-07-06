import { FileText } from "lucide-react";

export default function LibraryPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-24 text-center">
      <FileText className="size-10 text-muted-foreground" />
      <p className="text-lg font-medium">No documents yet</p>
      <p className="text-sm text-muted-foreground">Upload a PDF to start learning</p>
    </div>
  );
}
