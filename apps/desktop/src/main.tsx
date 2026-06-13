import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MarkApp } from "@mark/ui";
import "@mark/ui/styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <MarkApp />
  </StrictMode>
);
