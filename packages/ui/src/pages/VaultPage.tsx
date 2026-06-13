import { MemoryGraph } from "../components/vault/MemoryGraph";
import { VaultAddForm } from "../components/vault/VaultAddForm";

export function VaultPage() {
  return (
    <div className="h-full min-h-0 flex flex-col bg-matte">
      <VaultAddForm />
      <div className="flex-1 min-h-0">
        <MemoryGraph />
      </div>
    </div>
  );
}
