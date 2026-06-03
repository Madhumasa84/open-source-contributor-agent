"use client";

import { BrainCircuit, CheckCircle2, Server, WifiOff } from "lucide-react";
import clsx from "clsx";
import type { ProviderDescriptor, ProviderSelection } from "@/lib/types";

const roles = ["fix_proposal", "architecture_review", "risk_analysis", "alternative_implementation"];

export function ProviderMatrix({
  providers,
  selections,
  onChange
}: {
  providers: ProviderDescriptor[];
  selections: ProviderSelection[];
  onChange: (value: ProviderSelection[]) => void;
}) {
  function toggle(provider: ProviderDescriptor, model: string) {
    const exists = selections.some((item) => item.provider === provider.name && item.model === model);
    if (exists) {
      onChange(selections.filter((item) => !(item.provider === provider.name && item.model === model)));
      return;
    }
    onChange([...selections, { provider: provider.name, model, role: roles[selections.length % roles.length] }]);
  }

  return (
    <div className="grid gap-3 lg:grid-cols-2">
      {providers.map((provider) => (
        <section key={provider.name} className="rounded-md border border-line bg-white p-3">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2">
              {provider.capabilities.local ? (
                <Server aria-hidden className="h-4 w-4 text-steel" />
              ) : (
                <BrainCircuit aria-hidden className="h-4 w-4 text-pine" />
              )}
              <span className="truncate text-sm font-semibold capitalize">{provider.name}</span>
            </div>
            <span
              className={clsx(
                "inline-flex h-7 items-center gap-1 rounded-md border px-2 text-xs",
                provider.configured ? "border-pine/30 bg-mint text-pine" : "border-line bg-panel text-ink/60"
              )}
            >
              {provider.configured ? <CheckCircle2 aria-hidden className="h-3.5 w-3.5" /> : <WifiOff aria-hidden className="h-3.5 w-3.5" />}
              {provider.configured ? "Ready" : "Key"}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {provider.default_models.map((model) => {
              const active = selections.some((item) => item.provider === provider.name && item.model === model);
              return (
                <button
                  key={model}
                  type="button"
                  onClick={() => toggle(provider, model)}
                  className={clsx(
                    "h-8 rounded-md border px-2 text-xs transition",
                    active ? "border-pine bg-pine text-white" : "border-line bg-panel text-ink hover:border-pine/50"
                  )}
                  title={`${provider.name} ${model}`}
                >
                  {model}
                </button>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
