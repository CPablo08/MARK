import { Component, type ErrorInfo, type ReactNode } from "react";
import { motion } from "framer-motion";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("MARK UI error:", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="h-full flex items-center justify-center bg-matte p-8">
          <div className="max-w-md text-center">
            <h2 className="text-lg text-white mb-2">System error</h2>
            <p className="text-sm text-muted mb-4">{this.state.error.message}</p>
            <button
              type="button"
              onClick={() => this.setState({ error: null })}
              className="px-4 py-2 rounded border border-accent/30 text-accent text-sm"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
