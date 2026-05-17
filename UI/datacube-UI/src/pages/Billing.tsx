import { CreditCard, AlertTriangle } from "lucide-react";
import { Card, PageHeader } from "../components/ui/Card.tsx";
import { btnPrimaryCn } from "../lib/uiClasses.ts";

interface BillingData {
  plan: string;
  renewDate: string;
  stripePortal: string;
}

const DUMMY_BILLING_DATA: BillingData = {
  plan: "Pro plan",
  renewDate: "2024-12-31",
  stripePortal: "#",
};

const Billing = () => {
  const data: BillingData = DUMMY_BILLING_DATA;
  const isLoading = false;
  const error = false;

  if (isLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-[var(--text-muted)]">
        Loading billing…
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-[var(--danger)]">
        Could not load billing.
      </div>
    );
  }

  return (
    <div className="min-h-0 font-[var(--font-sans)] text-[var(--text-primary)]">
      <PageHeader
        title="Billing"
        description="Manage your plan and payment methods. (Placeholder data until Stripe is wired.)"
      />

      <div
        className="mb-8 flex items-start gap-3 rounded-[var(--radius-md)] border border-[var(--warning)]/35 bg-[var(--warning)]/10 px-4 py-3 text-sm text-[var(--text-primary)]"
        role="status"
      >
        <AlertTriangle
          className="mt-0.5 h-5 w-5 shrink-0 text-[var(--warning)]"
          aria-hidden
        />
        <p className="font-medium">
          This page is under development and shows sample data only.
        </p>
      </div>

      <Card className="relative overflow-hidden">
        <div className="pointer-events-none absolute -right-10 -top-10 h-48 w-48 rounded-full bg-[var(--accent-soft)] blur-3xl" />
        <div className="pointer-events-none absolute -bottom-10 -left-10 h-48 w-48 rounded-full bg-[var(--accent-soft)] blur-3xl opacity-60" />

        <div className="relative">
          <h2 className="mb-6 flex items-center gap-3 text-xl font-bold text-[var(--text-primary)]">
            <CreditCard className="h-7 w-7 text-[var(--accent-bright)]" />
            Current plan
          </h2>

          <div className="space-y-3 text-base">
            <p className="flex flex-wrap items-baseline gap-2">
              <span className="w-28 shrink-0 font-semibold text-[var(--text-muted)]">
                Plan
              </span>
              <span className="font-medium text-[var(--accent-bright)]">
                {data?.plan || "—"}
              </span>
            </p>
            <p className="flex flex-wrap items-baseline gap-2">
              <span className="w-28 shrink-0 font-semibold text-[var(--text-muted)]">
                Renews
              </span>
              <span className="text-[var(--text-primary)]">
                {data?.renewDate || "—"}
              </span>
            </p>
          </div>

          <div className="mt-8 flex flex-col gap-6 border-t border-[var(--border-subtle)] pt-6 sm:flex-row sm:items-center sm:justify-between">
            <p className="max-w-md text-sm text-[var(--text-muted)]">
              When live, you will open the billing portal to update payment
              methods, invoices, and subscription.
            </p>
            <a
              href={data?.stripePortal}
              target="_blank"
              rel="noopener noreferrer"
              className={btnPrimaryCn("inline-flex w-full shrink-0 sm:w-auto")}
            >
              Open billing portal
            </a>
          </div>
        </div>
      </Card>

      <p className="mt-10 text-center text-sm text-[var(--text-subtle)]">
        Need help? Contact support for account changes.
      </p>
    </div>
  );
};

export default Billing;
